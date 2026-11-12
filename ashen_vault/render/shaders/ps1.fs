#version 330

noperspective in vec2 fragTexCoord;
in vec3 fragLight;
in float fragDepth;

uniform sampler2D texture0;
uniform vec4 colDiffuse;
uniform vec3 fogColor;
uniform vec2 fogRange;   // start, end in meters

out vec4 finalColor;

const float bayer[16] = float[](
     0.0,  8.0,  2.0, 10.0,
    12.0,  4.0, 14.0,  6.0,
     3.0, 11.0,  1.0,  9.0,
    15.0,  7.0, 13.0,  5.0);

void main()
{
    vec4 tex = texture(texture0, fragTexCoord);
    if (tex.a < 0.5) discard;

    vec3 c = tex.rgb * colDiffuse.rgb * fragLight;
    float fog = clamp((fragDepth - fogRange.x) / (fogRange.y - fogRange.x), 0.0, 1.0);
    c = mix(c, fogColor, fog);

    // Quantize to 15-bit color with ordered dithering, like the PS1 GPU.
    ivec2 p = ivec2(gl_FragCoord.xy) % 4;
    float threshold = (bayer[p.y * 4 + p.x] / 16.0 - 0.5) / 31.0;
    c = floor(clamp(c + threshold, 0.0, 1.0) * 31.0 + 0.5) / 31.0;

    finalColor = vec4(c, 1.0);
}
