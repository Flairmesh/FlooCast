# FlooAuxInput.py — duplex on Windows/Linux; smooth split-stream on macOS (Apple Silicon).
# Public API:
#   - list_additional_inputs(), serialize_input_device()
#   - set_input(selection), set_blocksize(n), stop()
# Optional helper:
#   - set_output_mapping([3,4])  # force device channel mapping if needed

import sys
from typing import List, Dict, Optional, Sequence
import collections
import numpy as np
import sounddevice as sd

try:
    # Required only on macOS split-stream path
    import samplerate  # pip install samplerate  (brew install libsamplerate may be needed first)
except Exception:
    samplerate = None


class FlooAuxInput:
    # ---------- Defaults ----------
    TARGET_RATE = 48000
    FALLBACK_RATE = 44100
    DTYPE = "int16"                 # Windows/Linux default; macOS switched below
    LATENCY = None                  # overridden on macOS

    # Backend preference order
    if sys.platform == "win32":
        PREFERRED_INPUT_BACKENDS  = ["ASIO", "WASAPI", "WDM-KS", "DirectSound", "MME"]
        PREFERRED_OUTPUT_BACKENDS = ["WASAPI", "ASIO", "DirectSound", "MME", "WDM-KS"]
    elif sys.platform == "darwin":
        PREFERRED_INPUT_BACKENDS  = ["Core Audio"]
        PREFERRED_OUTPUT_BACKENDS = ["Core Audio"]
        DTYPE = "float32"           # CoreAudio prefers float
        LATENCY = "low"            # headroom for independent device clocks
    else:
        PREFERRED_INPUT_BACKENDS  = ["ALSA", "JACK", "PulseAudio"]
        PREFERRED_OUTPUT_BACKENDS = ["ALSA", "JACK", "PulseAudio"]

    # Windows: WASAPI shared by default
    PREFER_EXCLUSIVE_IN = False
    PREFER_EXCLUSIVE_OUT = False

    # Output auto-pick (name hints)
    OUTPUT_HINTS: Sequence[str] = ("FMA120", "QCC3086")

    # Hide these from input list
    INPUT_BLOCKLIST = ("FMA120", "QCC3086")

    _DISABLED = object()

    # ---------- Construction / config ----------
    @staticmethod
    def _platform_default_blocksize() -> int:
        if sys.platform == "win32":
            return 128
        if sys.platform == "darwin":
            return 1024   # Option B: calmer across two clocks
        return 256

    @staticmethod
    def _validate_blocksize(n: int) -> int:
        if not isinstance(n, int):
            raise ValueError("blocksize must be an integer")
        if n < 64:
            raise ValueError("blocksize too small (min 64)")
        if n > 4096:
            raise ValueError("blocksize too large (max 4096)")
        return n

    def __init__(self, blocksize: Optional[int] = None):
        # single duplex stream (Windows/Linux) OR split streams (macOS)
        self._stream: Optional[sd.Stream] = None
        self._in_stream: Optional[sd.InputStream] = None
        self._out_stream: Optional[sd.OutputStream] = None
        self._running = False

        self._cap_channels = 1
        self._pb_channels = 2
        self._rate = self.TARGET_RATE
        self._dtype = self.DTYPE

        self._input_sel: Optional[Dict] = None
        self._input_disabled = False

        # config
        self._blocksize = self._platform_default_blocksize() if blocksize is None else self._validate_blocksize(blocksize)

        # restart helpers
        self._last_start_name_hint: Optional[str] = None

        # diagnostics
        self._xruns = 0
        self._debug = False

        # split-stream state (macOS)
        self._rb = None
        self._asrc = None
        self._ratio = 1.0
        self._ratio_smoothed = 1.0
        self._mac_target_seconds  = 0.40
        self._mac_prefill_seconds = 0.25
        self._mac_resampler_name  = "sinc_fastest"

        # --- Option B PLL tuning (to eliminate "si-si") ---
        self._ppm_limit = 1000e-6   # ±1000 ppm clamp
        self._loop_gain = 0.001     # very gentle corrections
        self._ratio_alpha = 0.005   # strong smoothing of ratio
        self._deadband = 0.20       # ±20% around target ⇒ hold exactly 1.0
        self._target = 0

        # optional functional feature
        self._out_mapping = None        # e.g., [3,4]

    # ------- Optional helper -------
    def set_output_mapping(self, mapping: Optional[Sequence[int]]) -> None:
        """Optionally force output channel indices (1-based), e.g. [3,4]."""
        self._out_mapping = list(mapping) if mapping else None

    # -------------- Public API --------------

    def list_additional_inputs(self) -> List[Dict]:
        devs = self._sd_list_devices()
        chosen_backend = None
        available = {d["hostapi"] for d in devs if d["is_input"]}
        for b in self.PREFERRED_INPUT_BACKENDS:
            if b in available:
                chosen_backend = b
                break

        if chosen_backend:
            candidates = [d for d in devs if d["is_input"]
                          and d["hostapi"] == chosen_backend
                          and not self._is_blocklisted_input(d["name"])]
        else:
            candidates = [d for d in devs if d["is_input"]
                          and not self._is_blocklisted_input(d["name"])]

        out: List[Dict] = [{
            "id": None, "name": "None", "backend": "",
            "sample_rate": None, "max_channels": None,
        }]
        for d in candidates:
            out.append({
                "id": d["index"], "name": d["name"], "backend": d["hostapi"],
                "sample_rate": d["default_samplerate"], "max_channels": d["max_input_channels"],
            })
        return out

    def serialize_input_device(self, device: Optional[Dict]) -> Dict:
        if (not device) or (device.get("id") is None) or (device.get("name", "").strip().lower() == "none"):
            return {"id": None, "name": "None", "backend": ""}
        return {"id": device.get("id"), "name": device.get("name", ""), "backend": device.get("backend", "")}

    def set_input(self, selection: Optional[Dict]) -> None:
        was_running = self._running

        if selection is None or self._is_saved_disabled(selection):
            self._input_sel = {"id": None, "name": "None", "backend": ""}
            self._input_disabled = True
            if was_running:
                self.stop()
            print("[FlooAuxInput] Input set to 'None' → loop disabled.")
            return

        self._input_disabled = False
        self._input_sel = {
            "id": selection.get("id"),
            "name": selection.get("name", ""),
            "backend": selection.get("backend", ""),
        }

        if was_running:
            print("[FlooAuxInput] Input changed → restarting loop...")
            self.stop()

        name_hint = self._input_sel["name"] or None
        self._last_start_name_hint = name_hint
        self._start_loop_internal(name_hint=name_hint)

    def set_blocksize(self, blocksize: int) -> None:
        """Update blocksize (frames per block) and restart if running."""
        new_bs = self._validate_blocksize(blocksize)
        if new_bs == self._blocksize:
            return
        self._blocksize = new_bs
        print(f"[FlooAuxInput] Blocksize set → {new_bs}")
        if self._running:
            hint = self._last_start_name_hint
            self.stop()
            self._start_loop_internal(name_hint=hint)

    def stop(self) -> None:
        if not self._running:
            return
        try:
            for s in (self._in_stream, self._out_stream, self._stream):
                if s:
                    try:
                        s.stop()
                    except Exception:
                        pass
                    try:
                        s.close()
                    except Exception:
                        pass
        finally:
            self._in_stream = None
            self._out_stream = None
            self._stream = None
            self._rb = None
            self._asrc = None
            self._running = False
            print("[FlooAuxInput] Loop stopped.")

    # -------------- Internals --------------

    def _start_loop_internal(self, *, name_hint: Optional[str]) -> None:
        if self._input_disabled:
            print("[FlooAuxInput] Not starting: input is 'None'.")
            return

        dtype = self.DTYPE
        latency = self.LATENCY
        chosen_block = self._blocksize

        # -------- Resolve devices (by hint → selection → first-ok) --------
        add_in = (self._pick_best_input_for_hint(name_hint)
                  or self._resolve_input_by_selection_or_hint(self._input_sel, name_hint)
                  or self._first_ok_input())
        out_dev = self._pick_output(self.OUTPUT_HINTS)
        if add_in is None or out_dev is None:
            print("[FlooAuxInput] ERROR: No valid input or output device.")
            return

        # -------- Channels (auto stereo if available) --------
        in_dev_info = sd.query_devices(add_in["id"])
        out_dev_info = sd.query_devices(out_dev["id"])
        self._cap_channels = 2 if int(in_dev_info.get("max_input_channels", 1)) >= 2 else 1
        self._pb_channels = 2 if int(out_dev_info.get("max_output_channels", 2)) >= 2 else 1

        print(f"[FlooAuxInput] Using Input  : {add_in['name']} [{add_in['backend']}] ({self._cap_channels} ch)")
        print(f"[FlooAuxInput] Using Output : {out_dev['name']} [{out_dev['backend']}] ({self._pb_channels} ch)")

        # -------- WASAPI extra settings (shared by default) --------
        extra_in = extra_out = None
        try:
            if sys.platform.startswith("win"):
                if add_in["backend"] == "WASAPI":
                    WasapiSettings = sd.WasapiSettings  # type: ignore[attr-defined]
                    extra_in = WasapiSettings(exclusive=self.PREFER_EXCLUSIVE_IN)
                if out_dev["backend"] == "WASAPI":
                    WasapiSettings = sd.WasapiSettings  # type: ignore[attr-defined]
                    extra_out = WasapiSettings(exclusive=self.PREFER_EXCLUSIVE_OUT)
        except Exception:
            pass

        # -------- Pick a COMMON rate only (no resampler on duplex path) --------
        rate = self._pick_common_rate(add_in["id"], out_dev["id"], dtype,
                                      self._cap_channels, self._pb_channels)
        if rate is None:
            print("[FlooAuxInput] No common sample rate (48k or 44.1k). Not starting.")
            return
        self._rate = rate
        self._dtype = dtype

        # Decide engine: macOS split-stream (with ASRC) vs legacy duplex
        is_mac = sys.platform == "darwin"
        different_devices = (add_in["id"] != out_dev["id"])

        if is_mac and different_devices:
            self._start_split_streams_mac(add_in, out_dev, chosen_block, latency)
        else:
            self._start_duplex_legacy(add_in, out_dev, chosen_block, latency, extra_in, extra_out)

    # ---- Legacy single duplex stream (Windows/Linux, or same device) ----
    def _start_duplex_legacy(self, add_in, out_dev, chosen_block, latency, extra_in=None, extra_out=None):
        def duplex_cb(indata, outdata, frames, time_info, status):
            if status:
                self._xruns += 1
            # Channel-mapping only (no resample)
            if indata.shape[1] == outdata.shape[1]:
                outdata[:] = indata
                return
            if indata.shape[1] == 1 and outdata.shape[1] == 2:
                outdata[:, 0] = indata[:, 0]
                outdata[:, 1] = indata[:, 0]
                return
            if indata.shape[1] == 2 and outdata.shape[1] == 1:
                if indata.dtype == np.int16:
                    outdata[:, 0] = ((indata[:, 0].astype(np.int32) + indata[:, 1].astype(np.int32)) // 2).astype(np.int16)
                else:
                    outdata[:, 0] = 0.5 * (indata[:, 0] + indata[:, 1])

        kw = dict(
            device=(add_in["id"], out_dev["id"]),
            samplerate=self._rate,
            blocksize=chosen_block,
            dtype=self._dtype,
            channels=(self._cap_channels, self._pb_channels),
            latency=latency,
            callback=duplex_cb,
        )
        if extra_in is not None or extra_out is not None:
            kw["extra_settings"] = (extra_in, extra_out)

        sd.check_input_settings(device=add_in["id"], samplerate=self._rate,
                                channels=self._cap_channels, dtype=self._dtype)
        sd.check_output_settings(device=out_dev["id"], samplerate=self._rate,
                                 channels=self._pb_channels, dtype=self._dtype)

        self._stream = sd.Stream(**kw)
        self._stream.start()
        self._running = True
        print(f"[FlooAuxInput] Loop started @ {self._rate} Hz | block={chosen_block} | dtype={self._dtype} | latency={latency}")

    # ---- macOS split streams with adaptive resampler (Option B) ----
    def _start_split_streams_mac(self, add_in, out_dev, chosen_block, latency):
        if samplerate is None:
            print("[FlooAuxInput] WARNING: 'samplerate' package not installed. Falling back to duplex path.")
            return self._start_duplex_legacy(add_in, out_dev, chosen_block, latency)

        # Force float32 on CoreAudio for stability
        self._dtype = "float32"

        # Ring buffer ~1.0 s (mono). Prefill/target come from profile (with safe defaults).
        rb_capacity_sec = 1.0
        self._rb = collections.deque(maxlen=int(self._rate * rb_capacity_sec))
        prefill_s = float(getattr(self, "_mac_prefill_seconds", 0.25))
        target_s  = float(getattr(self, "_mac_target_seconds", 0.40))
        self._rb.extend(np.zeros(int(self._rate * prefill_s), dtype=np.float32))
        self._target = int(self._rate * target_s)
        self._xruns = 0

        # Adaptive SRC using profile-selected converter
        resamp_name = getattr(self, "_mac_resampler_name", "sinc_fastest")
        self._asrc = samplerate.Resampler(converter_type=resamp_name, channels=1)
        self._ratio = 1.0
        self._ratio_smoothed = 1.0
        # PLL params already on self: _deadband, _loop_gain, _ratio_alpha, _ppm_limit

        cap_ch = self._cap_channels
        pb_ch  = self._pb_channels

        print(f"[FlooAuxInput] (mac) split streams: {add_in['name']} -> {out_dev['name']}")

        def capture_cb(indata, frames, time_info, status):
            if status:
                self._xruns += 1
            # robust mono collapse (e.g., C525 is 1-ch)
            if indata.shape[1] == 1:
                mono = indata[:, 0]
            else:
                mono = 0.5 * (indata[:, 0] + indata[:, 1])
            self._rb.extend(np.asarray(mono, dtype=np.float32))

        def playback_cb(outdata, frames, time_info, status):
            if status:
                self._xruns += 1

            # Buffer fill & normalized error
            fill = len(self._rb)
            err  = (fill - self._target) / max(1, self._target)

            # Deadband: if close enough to target, hold ratio exactly at 1.0
            if abs(err) <= self._deadband:
                ratio_target = 1.0
            else:
                ratio_target = 1.0 + float(np.clip(self._loop_gain * err, -self._ppm_limit, self._ppm_limit))

            # Smoothed ratio to avoid audible steps
            self._ratio_smoothed = (1.0 - self._ratio_alpha) * self._ratio_smoothed + self._ratio_alpha * ratio_target
            self._ratio = self._ratio_smoothed

            # Plan input needed with headroom
            need_in = int(frames / min(self._ratio, 1.0)) + 128
            take = min(need_in, fill)
            if take <= 0:
                outdata.fill(0.0)
                return

            # Pull 'take' samples into contiguous array
            buf = np.empty(take, dtype=np.float32)
            for i in range(take):
                buf[i] = self._rb.popleft()

            y = self._asrc.process(buf, self._ratio, end_of_input=False)
            if y.shape[0] < frames:
                y = np.pad(y, (0, frames - y.shape[0]))
            else:
                y = y[:frames]

            # mono -> N channels
            ch = outdata.shape[1]
            if ch == 1:
                outdata[:, 0] = y
            elif ch == 2:
                outdata[:, 0] = y
                outdata[:, 1] = y
            else:
                for c in range(ch):
                    outdata[:, c] = y

        # Decide final output channels/mapping safely
        out_channels = pb_ch
        out_mapping = None
        if self._out_mapping:
            if pb_ch >= max(self._out_mapping):
                out_channels = len(self._out_mapping)
                out_mapping = list(self._out_mapping)
            else:
                print(f"[FlooAuxInput] Ignoring out_mapping {self._out_mapping}: device has only {pb_ch} channels")
                out_mapping = None
                out_channels = pb_ch

        print(f"[FlooAuxInput] Output config → channels={out_channels} mapping={out_mapping}")
        print(f"[FlooAuxInput] Loop started (split) @ {self._rate} Hz | block={chosen_block} | dtype=float32 | latency={latency}")

        # Validate and start split streams
        sd.check_input_settings(device=add_in["id"], samplerate=self._rate,
                                channels=cap_ch, dtype="float32")
        sd.check_output_settings(device=out_dev["id"], samplerate=self._rate,
                                 channels=out_channels, dtype="float32")

        self._in_stream = sd.InputStream(device=add_in["id"], samplerate=self._rate,
                                         blocksize=chosen_block, dtype="float32",
                                         channels=cap_ch, latency=latency,
                                         callback=capture_cb)

        out_kwargs = dict(device=out_dev["id"], samplerate=self._rate,
                          blocksize=chosen_block, dtype="float32",
                          channels=out_channels, latency=latency,
                          callback=playback_cb)
        if out_mapping is not None:
            out_kwargs["mapping"] = out_mapping

        self._out_stream = sd.OutputStream(**out_kwargs)

        self._in_stream.start()
        self._out_stream.start()
        self._stream = None
        self._running = True

    # -------------- Selection & Utilities --------------

    def _sd_list_devices(self) -> List[Dict]:
        def norm(name: str) -> str:
            n = (name or "").lower()
            if "wasapi" in n: return "WASAPI"
            if "directsound" in n: return "DirectSound"
            if n == "mme": return "MME"
            if "wdm-ks" in n: return "WDM-KS"
            if "asio" in n: return "ASIO"
            if "core audio" in n: return "Core Audio"
            if "alsa" in n: return "ALSA"
            if "jack" in n: return "JACK"
            if "pulse" in n: return "PulseAudio"
            return name or ""
        has = sd.query_hostapis()
        result = []
        for idx, d in enumerate(sd.query_devices()):
            backend_short = norm(has[d["hostapi"]]["name"])
            result.append({
                "index": idx,
                "name": d["name"],
                "hostapi": backend_short,
                "max_input_channels": int(d.get("max_input_channels", 0)),
                "max_output_channels": int(d.get("max_output_channels", 0)),
                "default_samplerate": float(d.get("default_samplerate", 0.0)) or None,
                "is_input": int(d.get("max_input_channels", 0)) > 0,
                "is_output": int(d.get("max_output_channels", 0)) > 0,
            })
        return result

    @staticmethod
    def _is_blocklisted_input(name: str) -> bool:
        return any(tok.lower() in (name or "").lower() for tok in FlooAuxInput.INPUT_BLOCKLIST)

    @staticmethod
    def _is_saved_disabled(saved: Dict) -> bool:
        return (not saved) or (saved.get("id") is None) or (saved.get("name", "").strip().lower() == "none")

    def _resolve_input_by_selection_or_hint(self, selection: Optional[Dict], hint: Optional[str]) -> Optional[Dict]:
        if selection and not self._is_saved_disabled(selection):
            current = self.list_additional_inputs()[1:]
            for d in current:
                if d["name"] == selection.get("name") and d["id"] == selection.get("id"):
                    return d
        if hint:
            for d in self._sd_list_devices():
                if d["is_input"] and hint.lower() in d["name"].lower() and not self._is_blocklisted_input(d["name"]):
                    return {
                        "id": d["index"], "name": d["name"], "backend": d["hostapi"],
                        "max_channels": d["max_input_channels"], "default_samplerate": d["default_samplerate"],
                    }
        return None

    def _first_ok_input(self) -> Optional[Dict]:
        items = self.list_additional_inputs()
        return items[1] if len(items) > 1 else None

    def _pick_output(self, hints: Sequence[str]) -> Optional[Dict]:
        # Try exact matches on preferred backends first, then substring matches.
        hints_l = [h.lower() for h in hints]
        devs = self._sd_list_devices()

        def match_exact(d): return any(d["name"].lower() == h for h in hints_l)
        def match_sub(d):   return any(h in d["name"].lower() for h in hints_l)

        for b in self.PREFERRED_OUTPUT_BACKENDS:
            for d in devs:
                if d["is_output"] and d["hostapi"] == b and match_exact(d):
                    if b != "WDM-KS":
                        return {
                            "id": d["index"], "name": d["name"], "backend": d["hostapi"],
                            "sample_rate": d["default_samplerate"], "max_channels": d["max_output_channels"],
                        }
        for b in self.PREFERRED_OUTPUT_BACKENDS:
            for d in devs:
                if d["is_output"] and d["hostapi"] == b and match_sub(d):
                    if b != "WDM-KS":
                        return {
                            "id": d["index"], "name": d["name"], "backend": d["hostapi"],
                            "sample_rate": d["default_samplerate"], "max_channels": d["max_output_channels"],
                        }
        for d in devs:
            if d["is_output"] and match_exact(d):
                return {
                    "id": d["index"], "name": d["name"], "backend": d["hostapi"],
                    "sample_rate": d["default_samplerate"], "max_channels": d["max_output_channels"],
                }
        for d in devs:
            if d["is_output"] and match_sub(d):
                return {
                    "id": d["index"], "name": d["name"], "backend": d["hostapi"],
                    "sample_rate": d["default_samplerate"], "max_channels": d["max_output_channels"],
                }
        return None

    def _pick_common_rate(self, in_idx: int, out_idx: int, dtype: str, ch_in: int, ch_out: int) -> Optional[int]:
        # Prefer device defaults if they match; then 48k, then 44.1k
        candidates = []
        try:
            rin = int(sd.query_devices(in_idx)["default_samplerate"])
            rout = int(sd.query_devices(out_idx)["default_samplerate"])
            if rin == rout:
                candidates.append(rin)
        except Exception:
            pass
        for r in (self.TARGET_RATE, self.FALLBACK_RATE):
            if r not in candidates:
                candidates.append(r)

        for r in candidates:
            ok_in = ok_out = False
            try:
                sd.check_input_settings(device=in_idx, samplerate=r, channels=ch_in, dtype=dtype); ok_in = True
            except Exception:
                ok_in = False
            try:
                sd.check_output_settings(device=out_idx, samplerate=r, channels=ch_out, dtype=dtype); ok_out = True
            except Exception:
                ok_out = False
            print(f"[FlooAuxInput] Rate check {r} Hz: IN={ok_in} OUT={ok_out}")
            if ok_in and ok_out:
                return r
        return None

    def _pick_best_input_for_hint(self, name_hint: Optional[str]) -> Optional[Dict]:
        if not name_hint:
            return None
        all_devs = self._sd_list_devices()
        candidates = [d for d in all_devs
                      if d["is_input"] and name_hint.lower() in d["name"].lower()
                      and not self._is_blocklisted_input(d["name"])]
        if not candidates:
            return None
        rank = {b: i for i, b in enumerate(self.PREFERRED_INPUT_BACKENDS)}
        candidates.sort(key=lambda d: (rank.get(d["hostapi"], 999), d["name"]))
        d = candidates[0]
        return {
            "id": d["index"], "name": d["name"], "backend": d["hostapi"],
            "max_channels": d["max_input_channels"], "default_samplerate": d["default_samplerate"],
        }

    def set_latency_profile_mac(self, profile: str = "low") -> None:
        """
        macOS-only latency profile selector. No effect on Windows/Linux.

        Profiles:
          - "safe":  largest buffer, maximum stability (closest to your current defaults)
          - "low":   balanced latency vs stability
          - "ultra": lowest latency; requires clean devices/USB
          - "jack":  JACK-like calm: bigger buffer, very gentle PLL, wide dead-band,
                     high-quality resampler to avoid artifacts when the ratio moves
        """
        if sys.platform != "darwin":
            return

        p = (profile or "low").strip().lower()

        if p == "safe":
            params = dict(
                blk=1024,
                target_s=0.40,   # ~400 ms target fill
                prefill_s=0.25,
                deadband=0.20,
                loop_gain=0.001,
                alpha=0.005,
                ppm=1000e-6,
                resamp="sinc_fastest"
            )
        elif p == "ultra":
            params = dict(
                blk=128,
                target_s=0.06,   # ~60 ms
                prefill_s=0.02,
                deadband=0.06,
                loop_gain=0.002,
                alpha=0.02,
                ppm=800e-6,
                resamp="sinc_medium"
            )
        elif p == "jack":
            params = dict(
                blk=512,
                target_s=0.25,   # ~250 ms
                prefill_s=0.15,
                deadband=0.25,
                loop_gain=0.0006,
                alpha=0.002,
                ppm=300e-6,
                resamp="sinc_best"
            )
        else:  # "low" (default)
            params = dict(
                blk=256,
                target_s=0.12,   # ~120 ms
                prefill_s=0.04,
                deadband=0.10,
                loop_gain=0.0015,
                alpha=0.01,
                ppm=600e-6,
                resamp="sinc_medium"
            )

        # Apply to the existing Option B path (only used on macOS with two devices):
        self._blocksize = params["blk"]
        self._deadband = params["deadband"]
        self._loop_gain = params["loop_gain"]
        self._ratio_alpha = params["alpha"]
        self._ppm_limit = params["ppm"]

        self._mac_target_seconds  = params["target_s"]
        self._mac_prefill_seconds = params["prefill_s"]
        self._mac_resampler_name  = params["resamp"]

        # If currently running, restart to apply
        if self._running:
            self.stop()
            self._start_loop_internal(name_hint=self._last_start_name_hint)

        print(f"[FlooAuxInput] macOS profile applied → {p} | block={params['blk']} | target={params['target_s']:.2f}s | resampler={params['resamp']}")
        
    def _apply_profile_params(
        self,
        *,
        blk: int,
        target_s: float,
        prefill_s: float,
        deadband: float,
        loop_gain: float,
        alpha: float,
        ppm: float,
        resamp: str,
    ) -> None:
        """Internal: apply macOS latency profile parameters and restart if needed."""
        # Core PLL / smoothing
        self._deadband = float(deadband)
        self._loop_gain = float(loop_gain)
        self._ratio_alpha = float(alpha)
        self._ppm_limit = float(ppm)

        # macOS split-stream specifics
        self._mac_target_seconds  = float(target_s)
        self._mac_prefill_seconds = float(prefill_s)
        self._mac_resampler_name  = str(resamp)

        # Blocksize used on next (re)start; does not modify Windows/Linux logic
        self._blocksize = int(blk)

        # If currently running, restart with the new parameters
        if self._running:
            self.stop()
            self._start_loop_internal(name_hint=self._last_start_name_hint)



