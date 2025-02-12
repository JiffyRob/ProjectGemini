#version 300 es

// This shader contains code by various authors.  Please see comments for details.
// Original until stated otherwise

precision highp float;

#include "planet_struct"
#include "planets"
#include "cnoise"

#line 13 4
// per pixel
in vec2 instance_coord;
flat in int planet_id;
in float frag_radius;
in float frag_time;

// parameters
PlanetAtmosphere atmosphere;
PlanetTerrain terrain;
PlanetPhysics physics;

layout (location = 0) out vec4 out_color;

// per frame
const vec3 light_direction = vec3(1, 0.5, -0.5);

// actually constant
const int TERRAIN_WATER = 1;
const int TERRAIN_LOW = 2;
const int TERRAIN_HIGH = 3;

const int STAR = 0;
const int PLANET_TERRA = 1;
const int PLANET_TERRA2 = 2;
const int PLANET_KEERGAN = 3;

// credit: Neil Mendoza
// https://www.neilmendoza.com/glsl-rotation-about-an-arbitrary-axis/
mat4 rotationMatrix(vec3 axis, float angle)
{
    axis = normalize(axis);
    float s = sin(angle);
    float c = cos(angle);
    float oc = 1.0 - c;
    
    return mat4(oc * axis.x * axis.x + c,           oc * axis.x * axis.y - axis.z * s,  oc * axis.z * axis.x + axis.y * s,  0.0,
                oc * axis.x * axis.y + axis.z * s,  oc * axis.y * axis.y + c,           oc * axis.y * axis.z - axis.x * s,  0.0,
                oc * axis.z * axis.x - axis.y * s,  oc * axis.y * axis.z + axis.x * s,  oc * axis.z * axis.z + c,           0.0,
                0.0,                                0.0,                                0.0,                                1.0);
}

// original code again
int get_terrain(float elevation, float high, float water) {
    if (elevation > high) {
        return TERRAIN_HIGH;
    }
    if (elevation > water) {
        return TERRAIN_LOW;
    }
    return TERRAIN_WATER;
}

void main() {
    // shading values
    vec3 p = vec3(instance_coord.xy, sqrt(0.25 - instance_coord.x * instance_coord.x - instance_coord.y * instance_coord.y));
    float theta = (pow((acos(max(dot(p, light_direction), 0.0)) / 3.14), 1.0));
    int index = 0;
    if (theta < 0.5) {
        index = 1;
    }
    // handle planet parameters
    configure_planet(planet_id, terrain, atmosphere, physics);
    float dist = distance(instance_coord, vec2(0.0));
    out_color = vec4(0.0);

    if (dist < physics.radius) {
        vec3 pp = (vec4(p.xyz, 1) * rotationMatrix(physics.rotation_axis, frag_time * physics.rotation_speed)).xyz;
        float elevation = (cnoise(vec3(terrain.seed) + pp * terrain.bumpiness) + 1.0) / 2.0;
        int terrain_type = get_terrain(elevation, terrain.high_level, terrain.water_level);
        switch (terrain_type) {
            case TERRAIN_WATER:
                out_color = vec4(terrain.water_colors[index].rgb / 255.0, 1.0);
                break;
            case TERRAIN_LOW:
                out_color = vec4(terrain.low_ground_colors[index].rgb / 255.0, 1.0);
                break;
            case TERRAIN_HIGH:
                out_color = vec4(terrain.high_ground_colors[index].rgb / 255.0, 1.0);
                break;
        }
    }
    if (dist < 0.5) {
      vec3 pp = vec3(instance_coord.xy, sqrt(0.25 - instance_coord.x * instance_coord.x - instance_coord.y * instance_coord.y));
        pp = (vec4(pp.xyz, 1) * rotationMatrix(physics.rotation_axis, frag_time * physics.rotation_speed * atmosphere.rotation_multiplier)).xyz;
        pp.x /= 3.0;
        vec3 point = vec3(terrain.seed);
        point.z += atmosphere.swirl_speed * frag_time;
        bool has_clouds = (cnoise(point + pp * atmosphere.swishiness) + 1.0) / 2.0 < atmosphere.cloudiness;
        if (has_clouds) {
            out_color = vec4(atmosphere.cloud_colors[index].rgb / 255.0, 1.0);
        }
        else if (dist > physics.radius) {
          discard;
        }
    }
    else {
      discard;
    }
}