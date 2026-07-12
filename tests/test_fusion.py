import json
from pios.core.fusion import fuse


def test_fusion_optional(tmp_path):
    (tmp_path/"external").mkdir()
    (tmp_path/"external"/"macro_radar_latest.json").write_text(json.dumps({"risk_score":60,"confidence":80}),encoding="utf-8")
    out=fuse(20,90,tmp_path)
    assert "macro" in out["available_radars"]
    assert out["fused_score"]>20
