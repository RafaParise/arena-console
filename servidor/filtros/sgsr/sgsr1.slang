#version 450

// Snapdragon Game Super Resolution 1 (SGSR 1), da Qualcomm, no formato de filtro do RetroArch (slang).
// Portado pelo ARENA em 12/11/2026 do sgsr1_shader_mobile.frag oficial
// (github.com/SnapdragonStudios/snapdragon-gsr, sgsr/v1/include/glsl), modo RGBA (o verde faz as vezes do brilho).
// A conta e' a mesma do original; mudam so a forma de receber o quadro (o "Source" do RetroArch no lugar do
// ps0/ViewportInfo) e os dois numeros fixos, que viram parametros (a nitidez e o limiar de borda).
//
// Um passo so, feito para a placa de video do celular: estica o quadro pequeno ate a tela e, onde ha borda,
// refaz o brilho com um Lanczos de 12 pontos dirigido pela borda; onde nao ha, fica o bilinear (barato).
//
// Copyright (c) 2025, Qualcomm Innovation Center, Inc. All rights reserved.
// SPDX-License-Identifier: BSD-3-Clause (o texto inteiro vai junto, em LICENSE.txt, nesta pasta).

layout(push_constant) uniform Push
{
    vec4 SourceSize;
    vec4 OriginalSize;
    vec4 OutputSize;
    uint FrameCount;
    float SGSR_NITIDEZ;
    float SGSR_BORDA;
} params;

#pragma parameter SGSR_NITIDEZ "SGSR: nitidez" 2.0 1.0 4.0 0.1
#pragma parameter SGSR_BORDA "SGSR: limiar de borda (de 0 a 255)" 8.0 1.0 32.0 1.0

layout(std140, set = 0, binding = 0) uniform UBO
{
    mat4 MVP;
} global;

#pragma stage vertex
layout(location = 0) in vec4 Position;
layout(location = 1) in vec2 TexCoord;
layout(location = 0) out vec2 vTexCoord;

void main()
{
    gl_Position = global.MVP * Position;
    vTexCoord = TexCoord;
}

#pragma stage fragment
layout(location = 0) in vec2 vTexCoord;
layout(location = 0) out vec4 FragColor;
layout(set = 0, binding = 2) uniform sampler2D Source;

float fastLanczos2(float x)
{
    float wA = x - 4.0;
    float wB = x * wA - wA;
    wA *= wA;
    return wB * wA;
}

vec2 weightY(float dx, float dy, float c, float std_)
{
    float x = ((dx * dx) + (dy * dy)) * 0.55 + clamp(abs(c) * std_, 0.0, 1.0);
    float w = fastLanczos2(x);
    return vec2(w, w * c);
}

void main()
{
    // ViewportInfo do original = (1/largura, 1/altura, largura, altura) do quadro de entrada.
    vec4 viewport = vec4(params.SourceSize.zw, params.SourceSize.xy);
    float edgeThreshold = params.SGSR_BORDA / 255.0;
    float edgeSharpness = params.SGSR_NITIDEZ;

    vec4 color = vec4(textureLod(Source, vTexCoord, 0.0).xyz, 0.0);

    vec2 imgCoord = (vTexCoord * viewport.zw) + vec2(-0.5, 0.5);
    vec2 imgCoordPixel = floor(imgCoord);
    vec2 coord = imgCoordPixel * viewport.xy;
    vec2 pl = imgCoord - imgCoordPixel;
    vec4 left = textureGather(Source, coord, 1);

    float edgeVote = abs(left.z - left.y) + abs(color.y - left.y) + abs(color.y - left.z);
    if (edgeVote > edgeThreshold)
    {
        coord.x += viewport.x;

        vec4 right = textureGather(Source, coord + vec2(viewport.x, 0.0), 1);
        vec4 upDown;
        upDown.xy = textureGather(Source, coord + vec2(0.0, -viewport.y), 1).wz;
        upDown.zw = textureGather(Source, coord + vec2(0.0, viewport.y), 1).yx;

        float mean = (left.y + left.z + right.x + right.w) * 0.25;
        left = left - vec4(mean);
        right = right - vec4(mean);
        upDown = upDown - vec4(mean);
        color.w = color.y - mean;

        float sum = (((((abs(left.x) + abs(left.y)) + abs(left.z)) + abs(left.w))
                    + (((abs(right.x) + abs(right.y)) + abs(right.z)) + abs(right.w)))
                    + (((abs(upDown.x) + abs(upDown.y)) + abs(upDown.z)) + abs(upDown.w)));
        float std_ = 2.181818 / sum;

        vec2 aWY = weightY(pl.x, pl.y + 1.0, upDown.x, std_);
        aWY += weightY(pl.x - 1.0, pl.y + 1.0, upDown.y, std_);
        aWY += weightY(pl.x - 1.0, pl.y - 2.0, upDown.z, std_);
        aWY += weightY(pl.x, pl.y - 2.0, upDown.w, std_);
        aWY += weightY(pl.x + 1.0, pl.y - 1.0, left.x, std_);
        aWY += weightY(pl.x, pl.y - 1.0, left.y, std_);
        aWY += weightY(pl.x, pl.y, left.z, std_);
        aWY += weightY(pl.x + 1.0, pl.y, left.w, std_);
        aWY += weightY(pl.x - 1.0, pl.y - 1.0, right.x, std_);
        aWY += weightY(pl.x - 2.0, pl.y - 1.0, right.y, std_);
        aWY += weightY(pl.x - 2.0, pl.y, right.z, std_);
        aWY += weightY(pl.x - 1.0, pl.y, right.w, std_);

        float finalY = aWY.y / aWY.x;

        float maxY = max(max(left.y, left.z), max(right.x, right.w));
        float minY = min(min(left.y, left.z), min(right.x, right.w));
        finalY = clamp(edgeSharpness * finalY, minY, maxY);

        float deltaY = finalY - color.w;

        // suaviza a entrada de contraste alto
        deltaY = clamp(deltaY, -23.0 / 255.0, 23.0 / 255.0);

        color.x = clamp(color.x + deltaY, 0.0, 1.0);
        color.y = clamp(color.y + deltaY, 0.0, 1.0);
        color.z = clamp(color.z + deltaY, 0.0, 1.0);
    }

    FragColor = vec4(color.xyz, 1.0);
}
