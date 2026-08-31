import React, { useEffect, useRef } from 'react';

const VERTEX_SHADER_SRC = `#version 300 es
in vec2 a_position;
out vec2 v_uv;

void main() {
  v_uv = (a_position + 1.0) * 0.5;
  gl_Position = vec4(a_position, 0.0, 1.0);
}
`;

const FRAGMENT_SHADER_SRC = `#version 300 es
precision highp float;

in vec2 v_uv;
out vec4 fragColor;

uniform vec2 u_resolution;
uniform float u_time;
uniform float u_intensity;

// Simplex 2D noise helper functions
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec3 permute(vec3 x) { return mod289(((x * 34.0) + 1.0) * x); }

float snoise(vec2 v) {
  const vec4 C = vec4(0.211324865405187,
                      0.366025403784439,
                     -0.577350269189626,
                      0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod289(i);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0))
    + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
  m = m * m;
  m = m * m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
  vec3 g;
  g.x  = a0.x  * x0.x  + h.x  * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

float fbm(vec2 st) {
  float v = 0.0;
  float a = 0.5;
  vec2 shift = vec2(100.0);
  mat2 rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.50));
  for (int i = 0; i < 3; ++i) {
    v += a * snoise(st);
    st = rot * st * 2.0 + shift;
    a *= 0.5;
  }
  return v;
}

void main() {
  vec2 st = gl_FragCoord.xy / u_resolution.xy;
  st.x *= u_resolution.x / u_resolution.y;

  // Very slow time-based color flow (time * 0.05)
  float t = u_time * 0.05;

  // Organic domain warping
  vec2 q = vec2(
    fbm(st * 0.75 + vec2(t * 0.35, t * 0.18)),
    fbm(st * 0.75 + vec2(-t * 0.25, t * 0.42))
  );

  vec2 r = vec2(
    fbm(st * 0.75 + 1.2 * q + vec2(1.7, 9.2) + 0.12 * t),
    fbm(st * 0.75 + 1.2 * q + vec2(8.3, 2.8) + 0.10 * t)
  );

  float f = fbm(st * 0.75 + 1.4 * r);
  f = clamp((f + 0.55) * 0.85, 0.0, 1.0);

  // Palette:
  // Deep near-black shadow #0F0D0A
  vec3 colNearBlack = vec3(0.059, 0.051, 0.039);
  // Deep charcoal #1A1815
  vec3 colCharcoal = vec3(0.102, 0.094, 0.082);
  // Warm brown #3A2A20
  vec3 colWarmBrown = vec3(0.227, 0.165, 0.125);
  // Brighter vermilion highlight #C4522A
  vec3 colVermilion = vec3(0.769, 0.322, 0.165);

  // Base gradient with true dark pockets for rich dynamic range
  vec3 color = mix(colNearBlack, colCharcoal, smoothstep(0.0, 0.40, f));
  color = mix(color, colWarmBrown, smoothstep(0.40, 0.80, f));

  // Focused, high-contrast vermilion highlights (firelight bleeding through smoke)
  float accentZone = pow(smoothstep(0.64, 0.95, f), 1.5) * smoothstep(0.1, 0.85, (r.x + 0.5) * 0.85);
  color = mix(color, colVermilion, clamp(accentZone * 0.65, 0.0, 0.85));

  // Subtle vignette
  vec2 uvNorm = v_uv * 2.0 - 1.0;
  float vignette = 1.0 - dot(uvNorm * 0.35, uvNorm * 0.35);
  color *= clamp(vignette, 0.75, 1.0);

  // Softened, subtle film grain (0.025 opacity, averaged over 2 sub-samples)
  float grain1 = fract(sin(dot(gl_FragCoord.xy + fract(u_time * 0.005), vec2(12.9898, 78.233))) * 43758.5453);
  float grain2 = fract(sin(dot(gl_FragCoord.xy + vec2(0.5, 0.5) + fract(u_time * 0.005), vec2(12.9898, 78.233))) * 43758.5453);
  float smoothGrain = (grain1 + grain2) * 0.5;
  color += (smoothGrain - 0.5) * 0.025;

  // Scale overall color intensity (1.0 on Intake hero, 0.65 on content-dense pages)
  fragColor = vec4(color * u_intensity, 1.0);
}
`;

export interface ShaderGradientBackgroundProps {
  intensity?: number;
}

export const ShaderGradientBackground: React.FC<ShaderGradientBackgroundProps> = ({
  intensity = 1.0,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const intensityRef = useRef(intensity);
  intensityRef.current = intensity;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || typeof window === 'undefined') return;

    const gl = canvas.getContext('webgl2', {
      alpha: false,
      depth: false,
      stencil: false,
      antialias: false,
      powerPreference: 'low-power',
    });

    if (!gl) {
      console.warn('WebGL2 not supported');
      return;
    }

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Compile shader helper
    const createShader = (type: number, src: string) => {
      const shader = gl.createShader(type);
      if (!shader) return null;
      gl.shaderSource(shader, src);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error('Shader compile error:', gl.getShaderInfoLog(shader));
        gl.deleteShader(shader);
        return null;
      }
      return shader;
    };

    const vertShader = createShader(gl.VERTEX_SHADER, VERTEX_SHADER_SRC);
    const fragShader = createShader(gl.FRAGMENT_SHADER, FRAGMENT_SHADER_SRC);
    if (!vertShader || !fragShader) return;

    const program = gl.createProgram();
    if (!program) return;
    gl.attachShader(program, vertShader);
    gl.attachShader(program, fragShader);
    gl.linkProgram(program);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error('Program link error:', gl.getProgramInfoLog(program));
      return;
    }

    gl.useProgram(program);

    // Fullscreen quad geometry
    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([
        -1.0, -1.0,
         1.0, -1.0,
        -1.0,  1.0,
        -1.0,  1.0,
         1.0, -1.0,
         1.0,  1.0,
      ]),
      gl.STATIC_DRAW
    );

    const posAttrLoc = gl.getAttribLocation(program, 'a_position');
    gl.enableVertexAttribArray(posAttrLoc);
    gl.vertexAttribPointer(posAttrLoc, 2, gl.FLOAT, false, 0, 0);

    const resolutionLoc = gl.getUniformLocation(program, 'u_resolution');
    const timeLoc = gl.getUniformLocation(program, 'u_time');
    const intensityLoc = gl.getUniformLocation(program, 'u_intensity');

    let width = 0;
    let height = 0;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      width = Math.floor(window.innerWidth * dpr * 0.75);
      height = Math.floor(window.innerHeight * dpr * 0.75);

      canvas.width = width;
      canvas.height = height;
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;

      gl.viewport(0, 0, width, height);
      gl.uniform2f(resolutionLoc, width, height);
      gl.uniform1f(intensityLoc, intensityRef.current);

      if (prefersReduced) {
        gl.uniform1f(timeLoc, 0.0);
        gl.drawArrays(gl.TRIANGLES, 0, 6);
      }
    };

    resize();
    window.addEventListener('resize', resize, { passive: true });

    if (prefersReduced) {
      return () => {
        window.removeEventListener('resize', resize);
        gl.deleteProgram(program);
        gl.deleteShader(vertShader);
        gl.deleteShader(fragShader);
        gl.deleteBuffer(positionBuffer);
      };
    }

    let animId = 0;
    const startTime = performance.now();
    let isVisible = document.visibilityState === 'visible';

    const handleVisibilityChange = () => {
      isVisible = document.visibilityState === 'visible';
      if (isVisible) {
        requestTick();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    const render = () => {
      if (!isVisible) return;

      const elapsed = (performance.now() - startTime) / 1000.0;
      gl.uniform1f(timeLoc, elapsed);
      gl.uniform1f(intensityLoc, intensityRef.current);
      gl.drawArrays(gl.TRIANGLES, 0, 6);

      animId = requestAnimationFrame(render);
    };

    const requestTick = () => {
      cancelAnimationFrame(animId);
      animId = requestAnimationFrame(render);
    };

    requestTick();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      gl.deleteProgram(program);
      gl.deleteShader(vertShader);
      gl.deleteShader(fragShader);
      gl.deleteBuffer(positionBuffer);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none select-none z-0"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 0,
        pointerEvents: 'none',
      }}
      aria-hidden="true"
    />
  );
};
