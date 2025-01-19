#version 300 es

precision highp float;

uniform bool blinkies;

flat in int planet_id;
in vec2 instance_coord;
in float frag_radius;

out vec4 out_color;

const vec4 STAR_COLORS[2] = vec4[] (
    vec4(0.98, 1.0, 0.72, 1.0),
    vec4(0.56, 0.78, 0.84, 1.0)
);

const float TOLERANCE = 0.02;
const float STAR_RADIUS = 0.1;
const float BLOOM_RADIUS = 0.01;
const float SPIKE_RADIUS = 0.02;
const float BLOOM_LEVEL = 5.0;

void main() {
    out_color = STAR_COLORS[planet_id];
    float dist = distance(instance_coord, vec2(0.0, 0.0));
    bool draw_spikes = (frag_radius >= SPIKE_RADIUS) && blinkies;
    bool draw_bloom = (frag_radius >= BLOOM_RADIUS) && blinkies;
    draw_spikes = draw_spikes && ((abs(instance_coord.x) < TOLERANCE) || (abs(instance_coord.y) < TOLERANCE));
    out_color.a = 1.0 - step(STAR_RADIUS, dist);
    out_color.a += mix(float(draw_bloom), 0.0, dist * 3.0);
    out_color.a += mix(float(draw_spikes), 0.0, dist * 2.0);
    out_color.a = float(int(out_color.a * BLOOM_LEVEL)) / BLOOM_LEVEL;
    if (out_color.a <= 0.01) {
        discard;
    }
    out_color.rgb *= out_color.a;
    out_color.a = 1.0;
}