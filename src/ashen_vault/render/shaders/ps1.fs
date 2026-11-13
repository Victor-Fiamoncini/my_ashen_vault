#version 330

noperspective in vec2 fragTexCoord;
in vec3 fragLight;
in float fragDepth;
in vec3 fragWorld;

uniform sampler2D texture0;
uniform vec4 colDiffuse;
uniform vec3 fogColor;
uniform vec2 fogRange;   // start, end in meters

// Death-to-ash: `ashen` bleaches the model toward gray, `dissolve` eats it away from the top of
// `dissolveSpan` (base y, height in world meters) down, leaving a thin band of glowing embers.
uniform float ashen;
uniform float dissolve;
uniform vec2 dissolveSpan;

out vec4 finalColor;

const float bayer[16] = float[](
     0.0,  8.0,  2.0, 10.0,
    12.0,  4.0, 14.0,  6.0,
     3.0, 11.0,  1.0,  9.0,
    15.0,  7.0, 13.0,  5.0);

float hash(vec3 p)
{
    return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
}

void main()
{
    vec4 tex = texture(texture0, fragTexCoord);
    if (tex.a < 0.5) discard;

    vec3 c = tex.rgb * colDiffuse.rgb * fragLight;

    if (ashen > 0.0) {
        float lum = dot(c, vec3(0.299, 0.587, 0.114));
        c = mix(c, vec3(lum * 1.1, lum * 1.05, lum) + 0.04, ashen);
    }
    if (dissolve > 0.0) {
        // Chunky 8 cm cells so the crumbling reads as PS1 blocks, not smooth noise.
        float n = hash(floor(fragWorld * 12.0));
        float h = clamp((fragWorld.y - dissolveSpan.x) / max(dissolveSpan.y, 0.001), 0.0, 1.0);
        float v = (1.0 - h) * 0.7 + n * 0.3;
        float cut = dissolve * 1.05;
        if (v < cut) discard;
        if (v < cut + 0.06) c = mix(vec3(1.0, 0.55, 0.18), vec3(1.0, 0.85, 0.5), n);
    }
    float fog = clamp((fragDepth - fogRange.x) / (fogRange.y - fogRange.x), 0.0, 1.0);
    c = mix(c, fogColor, fog);

    // Quantize to 15-bit color with ordered dithering, like the PS1 GPU.
    ivec2 p = ivec2(gl_FragCoord.xy) % 4;
    float threshold = (bayer[p.y * 4 + p.x] / 16.0 - 0.5) / 31.0;
    c = floor(clamp(c + threshold, 0.0, 1.0) * 31.0 + 0.5) / 31.0;

    finalColor = vec4(c, 1.0);
}
