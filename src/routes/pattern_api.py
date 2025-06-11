from fastapi import APIRouter, Request
import random

router = APIRouter(prefix="/v1/patterns", tags=["Pattern"])

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

patterns = [
    {
        "name": "blobDigitDither",
        "randomParams": lambda: {
            "cellSize": random.randint(3, 6),
            "frequency": round(random.uniform(0.01, 0.04), 4),
            "blobScale": round(random.uniform(2.0, 4.0), 2),
            "threshold": round(random.uniform(0.2, 0.5), 2),
            "scale": 1.0
        },
        "drawColor": True,
        "code": """
        function(x, y, p, ctx) {
            const cs = p.cellSize;
            const cx = Math.floor(x / cs) * cs;
            const cy = Math.floor(y / cs) * cs;

            // 중심 거리 계산
            const dx = cx - ctx.width / 2;
            const dy = cy - ctx.height / 2;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const maxDist = Math.sqrt((ctx.width / 2) ** 2 + (ctx.height / 2) ** 2);
            const t = dist / maxDist;

            // 너무 먼 영역은 아예 배경
            if (t > 0.9) {
                return [255, 255, 255];
            }

            // 일관된 공간 노이즈 기반 샘플링
            const val = ctx.noise(cx * p.frequency, cy * p.frequency)
                    + 0.5 * ctx.noise(cx * p.frequency * 2, cy * p.frequency * 2);
            const norm = val * p.blobScale;

            if (norm > p.threshold) {
                const strength = (norm - p.threshold) / (1 - p.threshold);

                // 🎨 색상: 채도 높은 보라~파랑 계열
                const r = 255 * (1 - strength * 0.8);
                const g = 100 + 150 * strength;
                const b = 255;

                // 거리 기반 크기 및 모양
                const dotScale = Math.pow(1 - t, 1.2);
                const dotSize = cs * dotScale;

                ctx.fill(r, g, b);
                ctx.save();
                ctx.translate(cx + cs / 2, cy + cs / 2);

                if (t < 0.4) {
                    ctx.rect(-dotSize / 2, -dotSize / 2, dotSize, dotSize);  // 중심부: 정사각형
                } else {
                    ctx.ellipse(0, 0, dotSize, dotSize);  // 외곽: 원형
                }

                ctx.restore();
                return null;
            } else {
                return [255, 255, 255];
            }
        }
        """
    },
    {
        "name": "spectralWaveStripes",
        "randomParams": lambda: {
            "stripeWidth": random.randint(1, 4),
            "amplitude": random.uniform(50, 150),
            "frequency": round(random.uniform(0.01, 0.03), 4),
            "colors": random.sample([[0, 150, 255], [255, 120, 0], [100, 255, 180]], 2),
            "centerFade": True,
            "scale": 1.0
        },
        "drawColor": True,
        "code": """
        function(x, y, p, ctx) {
            const cx = 200;
            const cy = 200;

            const stripeSpacing = p.stripeWidth * 2;
            if (Math.floor(x) % stripeSpacing > p.stripeWidth) return [255, 255, 255];

            // 🌀 정현파 + 노이즈로 왜곡된 파형
            const baseWave = ctx.sin(x * p.frequency) * p.amplitude;
            const noise = (ctx.noise(x * 0.01, y * 0.01) - 0.5) * p.amplitude * 1.2;  // ±60% amplitude
            const wave = baseWave + noise;

            const dist = Math.abs(y - (cy + wave));

            // ✨ fade: 중앙에서 밝고 멀어질수록 색상 전이
            const fade = Math.exp(-dist * 0.04);  // 더 날카롭게 fade

            // 🎨 color interpolation
            const c1 = p.colors[0], c2 = p.colors[1];
            const r = c1[0] * (1 - fade) + c2[0] * fade;
            const g = c1[1] * (1 - fade) + c2[1] * fade;
            const b = c1[2] * (1 - fade) + c2[2] * fade;

            return [r, g, b];
        }

        """
    },
    {
        "name": "grainWavePattern",
        "randomParams": lambda: {
            "frequency": round(random.uniform(0.005, 0.015), 4),
            "amplitude": random.randint(30, 80),
            "grain": round(random.uniform(0.1, 0.3), 2),
            "scale": 1.0
        },
        "drawColor": True,
        "code": """
        function(x, y, p, ctx) {
            let colorStrength = 0;
            const layerCount = 5; // 파도 개수
            const spacing = 80;   // 각 파도 사이 간격

            for (let i = 0; i < layerCount; i++) {
                const yOffset = i * spacing + ctx.noise(i * 10) * 50;
                const freq = p.frequency * (0.8 + ctx.noise(i) * 0.4); // 각 레이어 주파수 살짝 다르게
                const amp = p.amplitude * (0.8 + ctx.noise(i + 100) * 0.4);
                const wave = ctx.sin(x * freq + i * 100) * amp;
                const base = wave + yOffset + ctx.noise(x * 0.01 + i, y * 0.01 + i) * 40;

                if (y < base) {
                    const noiseVal = ctx.noise(x * 0.5 + i, y * 0.5 + i);
                    const grainStrength = Math.floor(noiseVal * 255 * p.grain);
                    colorStrength += grainStrength;
                }
            }

            if (colorStrength > 0) {
                // 색상 보정 (밝기 누적 제한)
                const final = Math.min(255, 120 + colorStrength / layerCount);
                return [0, final, 255];
            } else {
                return [255, 255, 255];
            }
        }
        """
    },
    {
        "name": "spectralGradient",
        "randomParams": lambda: {
            "frequency": round(random.uniform(0.002, 0.008), 4),
            "intensity": round(random.uniform(0.5, 1.0), 2),
            "bands": random.randint(3, 6),
            "scale": 1.0
        },
        "drawColor": True,
        "code": """
        function(x, y, p, ctx) {
            // 방향 지정 (예: ↘ 방향)
            const angle = Math.PI / 4; // 45도
            const dx = Math.cos(angle);
            const dy = Math.sin(angle);

            // 방향성 흐름 계산
            const projected = (x * dx + y * dy) * p.frequency;

            // 부드러운 노이즈 변형 추가
            const noise = ctx.noise(x * 0.005, y * 0.005) * 0.5;

            const t = Math.min(1, Math.max(0, projected + noise * p.intensity)); // 0~1 보간값

            // 🎨 두 색상 정의
            const c1 = [255, 200, 240];  // 밝은 분홍
            const c2 = [120, 180, 255];  // 밝은 파랑

            const r = c1[0] * (1 - t) + c2[0] * t;
            const g = c1[1] * (1 - t) + c2[1] * t;
            const b = c1[2] * (1 - t) + c2[2] * t;

            return [r, g, b];
        }
        """
    },
    {
        "name": "digitSilhouette",
        "randomParams": lambda: {
            "cellSize": random.choice([4, 6, 8]),
            "frequency": round(random.uniform(0.01, 0.05), 3),
            "threshold": round(random.uniform(0.3, 0.6), 2),
            "hue": random.randint(0, 360),
            "scale": 1.0
        },
        "drawColor": True,
        "code": """
        function(x, y, p, ctx) {
            const cs = p.cellSize;
            const cx = Math.floor(x / cs) * cs;
            const cy = Math.floor(y / cs) * cs;

            // 중심 위치 기준 정렬
            const gx = Math.floor(cx / cs);
            const gy = Math.floor(cy / cs);

            // 도트 + 스트라이프 혼합 패턴 (조건은 예시)
            const isStripe = gx % 4 === 0;  // 수직 줄무늬
            const isDot = (gx + gy) % 6 === 0;  // 격자 점

            if (isStripe || isDot) {
                // 💡 위치 기반으로 hue 변화 유지
                const h = ((p.hue + (cx + cy) * 0.05) % 360) / 360;
                const s = 1;
                const l = 0.5;
                const a = s * Math.min(l, 1 - l);
                const f = (n) => {
                    const k = (n + h * 12) % 12;
                    return l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
                };

                const r = f(0) * 255;
                const g = f(8) * 255;
                const b = f(4) * 255;

                return [r, g, b];
            } else {
                return [255, 255, 255];  // 배경
            }
        }
        """
    },
    {
        "name": "gridFractalGradient",
        "randomParams": lambda: {
            "cols": random.randint(5, 10),
            "rows": random.randint(5, 10),
            "color1": [random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)],
            "color2": [random.randint(0, 150), random.randint(0, 150), random.randint(0, 150)],
            "gradientDir": random.choice(["horizontal", "vertical"]),
            "scale": 1.0
        },
        "drawColor": True,
        "code": """
        function(x, y, p, ctx) {
        const cw = 400 / p.cols;
        const ch = 400 / p.rows;

        const colIdx = Math.floor(x / cw);
        const rowIdx = Math.floor(y / ch);

        const localX = x % cw;
        const localY = y % ch;

        const inBox = true; // optional: introduce spacing later

        if (inBox) {
            let t;
            if (p.gradientDir === "horizontal") {
            t = localX / cw;
            } else {
            t = localY / ch;
            }

            const r = p.color1[0] * (1 - t) + p.color2[0] * t;
            const g = p.color1[1] * (1 - t) + p.color2[1] * t;
            const b = p.color1[2] * (1 - t) + p.color2[2] * t;

            return [r, g, b];
        } else {
            return [255, 255, 255];
        }
        }
        """
    }


]
