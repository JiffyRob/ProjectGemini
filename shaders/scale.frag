#version 300 es

precision highp float;
precision highp sampler2D;

uniform sampler2D input_texture;

layout (location = 0) out vec4 out_color;

in vec2 pygame_coord;

void main() {
    out_color = texture(input_texture, pygame_coord);
}