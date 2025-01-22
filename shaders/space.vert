#version 300 es

precision highp float;

layout (location=0) in vec3 loc;
layout (location=1) in int planet_id_;
layout (location=2) in vec2 vertex;
layout (location=3) in float radius;

layout (std140) uniform Common {
    vec4 viewpos;
    vec4 rot_vector;
    float near_z;
    float far_z;
    float time;
    float blah;
};

out vec2 instance_coord;
flat out int planet_id;
out float frag_radius;
out float frag_time;

void main() {
    // imagine using matrices...HAH!
    vec3 moved = loc;
    // translate point
    moved -= vec3(viewpos.x, viewpos.y, viewpos.z);
    // rotate point
    vec3 rotvec = -vec3(rot_vector.x, rot_vector.y, rot_vector.z);
    vec3 cross_product = cross(rotvec, moved);
    moved = moved + (cross_product * 2.0 * rot_vector.w) + (2.0 * cross(rotvec, cross_product));
    // z scaling
    float scale_factor = near_z / moved.z;
    float scaled_radius = radius * scale_factor;
    moved.xy *= scale_factor;
    moved.z = (moved.z - near_z) * 2.0 / (far_z - near_z) - 1.0;
    // X, Y scaling
    // moved.x *= 1.0 / 256.0;
    // moved.y *= 1.0 / 256.0;
    // don't ask why I multiply and divide by 2 here
    // (I don't know)
    gl_Position = vec4(moved.xy + vertex * scaled_radius * 2.0, moved.z, 1.0 + float(planet_id_) * 0.0001);
    instance_coord = vertex / 2.0;
    planet_id = planet_id_;
    frag_radius = scaled_radius;
    frag_time = time;
}