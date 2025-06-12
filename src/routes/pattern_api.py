from fastapi import APIRouter, Request, Body
from pydantic import BaseModel
import random

from src.service.scripts.ai.llm_ops_manager import OpsLLMManager

router = APIRouter(prefix="/v1/patterns", tags=["Pattern"])

# ---- 요청 바디 스키마 정의 ----
class PatternTranslateRequest(BaseModel):
    code: str  # JS function(x, y, p, ctx)

@router.get("/create")
async def get_random_pattern(request: Request):
    ctx = request.app.state.ctx
    pattern = random.choice(patterns)
    params = pattern["randomParams"]()
    result = {
        "name": pattern["name"],
        "defaultParams": params,
        "code": pattern["code"],
        "drawColor": pattern.get("drawColor", False)
    }

    ctx.log.info(f"[API]     - Generated pattern '{pattern['name']}' with params={params}, drawColor={result['drawColor']}")
    return result

@router.post("/translate")
async def translate_pattern(request: Request, body: PatternTranslateRequest):
    """
    사용자 JS draw 함수를 받아 patterns[] 항목 포맷으로 변환
    """
    ctx = request.app.state.ctx
    llm = ctx.llm_manager["ops"]
    result = await llm.convert_pattern(body.code)

    return {
        "success": True,
        "result": result
    }


# TODO function을 그대로 보내서 실행시키기 때문에 외부에서 여기에 이상한 function 주입하면 해킹당할수도,,,
# 일단 function 그대로 작성해서 보내기. create > get pattern template 뭐 이렇게 2중으로 구현해야할지도
patterns = [
    {
        "name": "meltingScanline",
        "randomParams": lambda: {
            "spots": [
                {
                    "x": random.randint(100, 500),
                    "y": random.randint(100, 500),
                    "radius": random.uniform(100, 150),
                    "intensity": random.uniform(0.8, 1.2),
                    "stretchY": random.uniform(0.6, 0.85)
                }
                for _ in range(random.randint(3, 4))
            ],
            "scanlineGap": random.randint(4, 6),
            "scanlineHue": random.randint(120, 260),
            "scale": 1.0
        },
        "drawColor": True,
        "code": """
        function(x, y, p, ctx) {
            function hsvToRgb(h, s, v) {
                const c = v * s;
                const m = v - c;
                const hp = h / 60;
                const k = hp % 6;
                const x = c * (1 - Math.abs(hp % 2 - 1));
                let r = 0, g = 0, b = 0;

                if (hp < 1)      { r = c; g = x; b = 0; }
                else if (hp < 2) { r = x; g = c; b = 0; }
                else if (hp < 3) { r = 0; g = c; b = x; }
                else if (hp < 4) { r = 0; g = x; b = c; }
                else if (hp < 5) { r = x; g = 0; b = c; }
                else             { r = c; g = 0; b = x; }

                return [(r + m) * 255, (g + m) * 255, (b + m) * 255];
            }

            let maxFalloff = 0;
            for (let i = 0; i < p.spots.length; i++) {
                const s = p.spots[i];
                const dx = x - s.x;
                const dy = (y - s.y) / s.stretchY;
                const r2 = s.radius * s.radius;
                const d2 = dx * dx + dy * dy;
                const fall = Math.exp(-Math.pow(d2 / r2, 1.5)) * s.intensity;
                if (fall > maxFalloff) maxFalloff = fall;
            }

            if (maxFalloff < 0.01) return [0, 0, 0];

            const brightness = maxFalloff * (y % p.scanlineGap === 0 ? 1.0 : 0.2);
            const value = Math.pow(brightness, 0.6);
            const sat = 1.0 - Math.pow(brightness, 6.5);

            const [r, g, b] = hsvToRgb(p.scanlineHue, sat, value);
            return [r, g, b];
        }
        """
    },
    {
        "name": "semiCircleGrid",
        "randomParams": lambda: {
            "cellSize": 40,
            "cols": 10,
            "rows": 10,
            "rotationSet": [0, 90, 180, 270],
            "fgColor": "#ffffff",
            "bgColor": "#1e1e1e",
            "scale": 1.0
        },
        "drawColor": True,
        "code": """
            function(x, y, p, ctx) {
                function hexToRgb(hex) {
                    hex = hex.replace('#', '');
                    const bigint = parseInt(hex, 16);
                    return [
                        (bigint >> 16) & 255,
                        (bigint >> 8) & 255,
                        bigint & 255
                    ];
                }

                const cs = p.cellSize;
                const col = Math.floor(x / cs);
                const row = Math.floor(y / cs);
                const index = row * p.cols + col;

                const angle = p.rotationSet[index % p.rotationSet.length];
                const cx = col * cs + cs / 2;
                const cy = row * cs + cs / 2;

                const dx = x - cx;
                const dy = y - cy;

                let rx = 0, ry = 0;
                if (angle === 0)       { rx = dx;  ry = dy; }
                else if (angle === 90)  { rx = dy;  ry = -dx; }
                else if (angle === 180) { rx = -dx; ry = -dy; }
                else if (angle === 270) { rx = -dy; ry = dx; }

                const inSemiCircle = ry < 0 && (rx * rx + ry * ry <= (cs / 2) * (cs / 2));
                return inSemiCircle ? hexToRgb(p.fgColor) : hexToRgb(p.bgColor);
            }
        """
    },
    {
        "name": "metaMounds",
        "randomParams": lambda: {
            "seed": random.randint(0, 9999),
            "frequency": round(random.uniform(0.002, 0.01), 4),
            "threshold": round(random.uniform(0.3, 0.55), 2),
            "amplitude": round(random.uniform(0.8, 1.4), 2),
            "scale": 1.0,
            "hue": random.randint(0, 360),         
            "saturation": round(random.uniform(0.6, 1.0), 2), 
            "value": round(random.uniform(0.7, 1.0), 2)     
        },
        "drawColor": True,
        "code": """
        function(x, y, p, ctx) {
        ctx.noiseSeed(p.seed);
        const nx = x * p.frequency;
        const ny = y * p.frequency;
        const h = ctx.noise(nx, ny); // 0~1

        const radius = h * p.amplitude * 200;  // 높이에 따라 반경 결정
        const cx = Math.floor(x / radius) * radius;
        const cy = Math.floor(y / radius) * radius;

        const dx = x - cx;
        const dy = y - cy;
        const d = Math.sqrt(dx*dx + dy*dy);
        const m = Math.exp(-Math.pow(d / radius, 2));

        if (m < p.threshold) return [0, 0, 0];

        const sat = p.saturation;
        const val = m * p.value;

        const c = hsvToRgb(p.hue, sat, val);
        return c;

        function hsvToRgb(h, s, v) {
            const c = v * s;
            const m = v - c;
            const hp = h / 60;
            const x = c * (1 - Math.abs(hp % 2 - 1));
            let r=0, g=0, b=0;
            if (hp < 1)      { r = c; g = x; b = 0; }
            else if (hp < 2) { r = x; g = c; b = 0; }
            else if (hp < 3) { r = 0; g = c; b = x; }
            else if (hp < 4) { r = 0; g = x; b = c; }
            else if (hp < 5) { r = x; g = 0; b = c; }
            else             { r = c; g = 0; b = x; }
            return [(r + m) * 255, (g + m) * 255, (b + m) * 255];
        }
        }
        """
    }
]