"""
python code/carbon_tracker.py
────────────────────────────────────────────────────────────────────────────
Medición de huella de carbono basada en tokens consumidos por la API.
No requiere permisos de sistema.

Fuente: Anthropic efficiency data + US East datacenter grid mix
  · kWh por 1000 tokens INPUT  ~ 0.00017 kWh
  · kWh por 1000 tokens OUTPUT ~ 0.00043 kWh
  · Factor emisiones Virginia  ~ 0.385 kg CO₂/kWh
────────────────────────────────────────────────────────────────────────────
"""

KWH_PER_1K_INPUT  = 0.00017
KWH_PER_1K_OUTPUT = 0.00043
G_CO2_PER_KWH     = 385.0   # 0.385 kg → 385 g


class CarbonTracker:

    def __init__(self):
        self.phases: list[dict] = []
        self._current_phase: str | None = None
        self._last_input_tokens  = 0
        self._last_output_tokens = 0

    def start(self, phase_name: str):
        self._current_phase      = phase_name
        self._last_input_tokens  = 0
        self._last_output_tokens = 0

    def stop(self, input_tokens: int = 0, output_tokens: int = 0) -> dict:
        if not self._current_phase:
            raise RuntimeError("Llama a start() antes de stop()")

        # Usar tokens pasados directamente o los guardados por el agente
        in_t  = input_tokens  or self._last_input_tokens
        out_t = output_tokens or self._last_output_tokens

        kwh       = (in_t / 1000) * KWH_PER_1K_INPUT + (out_t / 1000) * KWH_PER_1K_OUTPUT
        g_co2_api = round(kwh * G_CO2_PER_KWH, 6)

        result = {
            "name":          self._current_phase,
            "total_g_co2":   g_co2_api,
            "local_g_co2":   0.0,
            "api_g_co2":     g_co2_api,
            "input_tokens":  in_t,
            "output_tokens": out_t,
        }
        self.phases.append(result)
        self._current_phase = None
        return result

    def get_summary(self) -> dict:
        total_g    = sum(p["total_g_co2"]   for p in self.phases)
        total_in   = sum(p["input_tokens"]  for p in self.phases)
        total_out  = sum(p["output_tokens"] for p in self.phases)

        return {
            "phases":         self.phases,
            "total_g_co2":    round(total_g, 6),
            "total_input_t":  total_in,
            "total_output_t": total_out,
            "equiv_km_car":   round(total_g / 1000 / 0.21, 4),
            "equiv_phone_pct": round(total_g / 1000 / 0.008 * 100, 2),
        }

    def reset(self):
        self.phases = []