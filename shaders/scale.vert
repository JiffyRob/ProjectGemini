#version 300 es

precision highp float;
precision lowp int;

vec2 vertices[4] = vec2[](
    vec2(-1.0, 1.0),
    vec2(-1.0, -1.0),
    vec2(1.0, 1.0),
    vec2(1.0, -1.0)
);

vec2 surface_coords[4] = vec2[](
    vec2(0, 0),
    vec2(0, 1),
    vec2(1, 0),
    vec2(1, 1)
);

out vec2 pygame_coord;

void main() {
    gl_Position = vec4(vertices[gl_VertexID], 0.0, 1.0);
    pygame_coord = surface_coords[gl_VertexID];
}