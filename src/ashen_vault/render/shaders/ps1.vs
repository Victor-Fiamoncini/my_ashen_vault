#version 330

in vec3 vertexPosition;
in vec2 vertexTexCoord;
in vec3 vertexNormal;
in vec4 vertexColor;

uniform mat4 mvp;
uniform mat4 matModel;

uniform vec2 snapRes;      // grid that vertices snap to (PS1 integer screen coords)
uniform float isModel;     // 1 = lit by modelLight + normal, 0 = baked vertex light
uniform vec3 modelLight;
uniform vec3 torchColor;
uniform float torchRadius;

noperspective out vec2 fragTexCoord; // affine texture mapping
out vec3 fragLight;
out float fragDepth;

void main()
{
    vec4 clip = mvp * vec4(vertexPosition, 1.0);
    if (clip.w > 0.0) {
        vec2 ndc = clip.xy / clip.w;
        ndc = floor(ndc * snapRes + 0.5) / snapRes;
        clip.xy = ndc * clip.w;
    }
    gl_Position = clip;
    fragTexCoord = vertexTexCoord;

    float depth = max(clip.w, 0.0);
    float torch = clamp(1.0 - depth / max(torchRadius, 0.001), 0.0, 1.0);

    vec3 base;
    if (isModel > 0.5) {
        vec3 n = normalize(mat3(matModel) * vertexNormal);
        float shade = 0.55 + 0.45 * max(dot(n, normalize(vec3(0.35, 1.0, 0.25))), 0.0);
        base = modelLight * shade;
    } else {
        base = vertexColor.rgb;
    }
    fragLight = base + torchColor * torch;
    fragDepth = depth;
}
