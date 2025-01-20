#version 300 es

// This shader contains code by various authors.  Please see comments for details.
// Original until stated otherwise

precision highp float;

// per pixel
in vec2 instance_coord;
flat in int planet_id;
flat in int flippy;
in float frag_radius;
in float frag_time;

// parameters
float terrain_seed = 100.0;
float bumpiness = 5.0;
float water_level = 0.4;
float high_level = 0.66;
float cloudiness = 0.4;
float swishiness = 10.0;
float cloud_height = 0.02;
float swirly_speed = 0.2;
vec3 rotation_axis = vec3(0, 1, 0);
float rotation_speed = 0.2;
float cloud_rotation_speed = 0.13;

vec3[2] water_colors = vec3[](
    vec3(0.31, 0.64, 0.72),
    vec3(0.25, 0.29, 0.49)
);

vec3[2] low_ground_colors = vec3[](
    vec3(0.18, 0.34, 0.33),
    vec3(0.16, 0.21, 0.25)
);

vec3[2] high_ground_colors = vec3[](
    vec3(0.39, 0.67, 0.25),
    vec3(0.23, 0.49, 0.31)
);

vec3[2] cloud_colors = vec3[](
    vec3(0.96, 1.0, 0.91),
    vec3(0.87, 0.88, 0.91)
);

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

const vec4 STAR_COLORS[2] = vec4[](
  vec4(0.98, 1.0, 0.72, 1.0),
  vec4(0.56, 0.78, 0.84, 1.0)
);

//
// GLSL textureless classic 3D noise "cnoise",
// with an RSL-style periodic variant "pnoise".
// Author:  Stefan Gustavson (stefan.gustavson@liu.se)
// Version: 2024-11-07
//
// Many thanks to Ian McEwan of Ashima Arts for the
// ideas for permutation and gradient selection.
//
// Copyright (c) 2011 Stefan Gustavson. All rights reserved.
// Distributed under the MIT license. See LICENSE file.
// https://github.com/stegu/webgl-noise
//

vec3 mod289(vec3 x)
{
  return x - floor(x * (1.0 / 289.0)) * 289.0;
}

vec4 mod289(vec4 x)
{
  return x - floor(x * (1.0 / 289.0)) * 289.0;
}

vec4 permute(vec4 x)
{
  return mod289(((x*34.0)+10.0)*x);
}

vec4 taylorInvSqrt(vec4 r)
{
  return 1.79284291400159 - 0.85373472095314 * r;
}

vec3 fade(vec3 t) {
  return t*t*t*(t*(t*6.0-15.0)+10.0);
}

// Classic Perlin noise
float cnoise(vec3 P)
{
  vec3 Pi0 = floor(P); // Integer part for indexing
  vec3 Pi1 = Pi0 + vec3(1.0); // Integer part + 1
  Pi0 = mod289(Pi0);
  Pi1 = mod289(Pi1);
  vec3 Pf0 = fract(P); // Fractional part for interpolation
  vec3 Pf1 = Pf0 - vec3(1.0); // Fractional part - 1.0
  vec4 ix = vec4(Pi0.x, Pi1.x, Pi0.x, Pi1.x);
  vec4 iy = vec4(Pi0.yy, Pi1.yy);
  vec4 iz0 = Pi0.zzzz;
  vec4 iz1 = Pi1.zzzz;

  vec4 ixy = permute(permute(ix) + iy);
  vec4 ixy0 = permute(ixy + iz0);
  vec4 ixy1 = permute(ixy + iz1);

  vec4 gx0 = ixy0 * (1.0 / 7.0);
  vec4 gy0 = fract(floor(gx0) * (1.0 / 7.0)) - 0.5;
  gx0 = fract(gx0);
  vec4 gz0 = vec4(0.5) - abs(gx0) - abs(gy0);
  vec4 sz0 = step(gz0, vec4(0.0));
  gx0 -= sz0 * (step(0.0, gx0) - 0.5);
  gy0 -= sz0 * (step(0.0, gy0) - 0.5);

  vec4 gx1 = ixy1 * (1.0 / 7.0);
  vec4 gy1 = fract(floor(gx1) * (1.0 / 7.0)) - 0.5;
  gx1 = fract(gx1);
  vec4 gz1 = vec4(0.5) - abs(gx1) - abs(gy1);
  vec4 sz1 = step(gz1, vec4(0.0));
  gx1 -= sz1 * (step(0.0, gx1) - 0.5);
  gy1 -= sz1 * (step(0.0, gy1) - 0.5);

  vec3 g000 = vec3(gx0.x,gy0.x,gz0.x);
  vec3 g100 = vec3(gx0.y,gy0.y,gz0.y);
  vec3 g010 = vec3(gx0.z,gy0.z,gz0.z);
  vec3 g110 = vec3(gx0.w,gy0.w,gz0.w);
  vec3 g001 = vec3(gx1.x,gy1.x,gz1.x);
  vec3 g101 = vec3(gx1.y,gy1.y,gz1.y);
  vec3 g011 = vec3(gx1.z,gy1.z,gz1.z);
  vec3 g111 = vec3(gx1.w,gy1.w,gz1.w);

  vec4 norm0 = taylorInvSqrt(vec4(dot(g000, g000), dot(g010, g010), dot(g100, g100), dot(g110, g110)));
  vec4 norm1 = taylorInvSqrt(vec4(dot(g001, g001), dot(g011, g011), dot(g101, g101), dot(g111, g111)));

  float n000 = norm0.x * dot(g000, Pf0);
  float n010 = norm0.y * dot(g010, vec3(Pf0.x, Pf1.y, Pf0.z));
  float n100 = norm0.z * dot(g100, vec3(Pf1.x, Pf0.yz));
  float n110 = norm0.w * dot(g110, vec3(Pf1.xy, Pf0.z));
  float n001 = norm1.x * dot(g001, vec3(Pf0.xy, Pf1.z));
  float n011 = norm1.y * dot(g011, vec3(Pf0.x, Pf1.yz));
  float n101 = norm1.z * dot(g101, vec3(Pf1.x, Pf0.y, Pf1.z));
  float n111 = norm1.w * dot(g111, Pf1);

  vec3 fade_xyz = fade(Pf0);
  vec4 n_z = mix(vec4(n000, n100, n010, n110), vec4(n001, n101, n011, n111), fade_xyz.z);
  vec2 n_yz = mix(n_z.xy, n_z.zw, fade_xyz.y);
  float n_xyz = mix(n_yz.x, n_yz.y, fade_xyz.x); 
  return 2.2 * n_xyz;
}

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
int get_terrain(float elevation) {
    if (elevation > high_level) {
        return TERRAIN_HIGH;
    }
    if (elevation > water_level) {
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
    float dist = distance(instance_coord, vec2(0.0));
    switch (planet_id) {
        case STAR:
          out_color = vec4(0.0);
          if (dist < 0.5) {
            out_color = STAR_COLORS[flippy];
          }
          return;
        case PLANET_TERRA:
          break;
        case PLANET_TERRA2:
          terrain_seed = 75.0;
          cloudiness = 0.5;
          swirly_speed = 0.4;
          break;
        case PLANET_KEERGAN:
          // TODO: Find good shading colors
          high_ground_colors[0] = vec3(0.80, 0.14, 0.14);
          high_ground_colors[1] = vec3(0.80, 0.14, 0.14);
          low_ground_colors[0] = vec3(0.43, 0.15, 0.15);
          low_ground_colors[1] =  vec3(0.43, 0.15, 0.15);
          water_colors[0] = vec3(0.50, 0.31, 0.18);
          water_colors[1] = vec3(0.50, 0.31, 0.18);
          cloud_colors[0] = vec3(0.97, 0.80, 0.49);
          cloud_colors[1] = vec3(0.78, 0.56, 0.31);
          cloudiness = 0.5;
          swirly_speed = 0.35;
          terrain_seed = 0.0;
    }
    out_color = vec4(0.0);
    // planet rendering
    float planet_radius = 0.5 - cloud_height;
    if (dist < planet_radius) {
        vec3 pp = (vec4(p.xyz, 1) * rotationMatrix(rotation_axis, frag_time * rotation_speed)).xyz;
        float elevation = (cnoise(vec3(terrain_seed) + pp * bumpiness) + 1.0) / 2.0;
        int terrain = get_terrain(elevation);
        switch (terrain) {
            case TERRAIN_WATER:
                out_color = vec4(water_colors[index].rgb, 1.0);
                break;
            case TERRAIN_LOW:
                out_color = vec4(low_ground_colors[index].rgb, 1.0);
                break;
            case TERRAIN_HIGH:
                out_color = vec4(high_ground_colors[index].rgb, 1.0);
                break;
        }
    }
    if (dist < 0.5) {
      vec3 pp = vec3(instance_coord.xy, sqrt(0.25 - instance_coord.x * instance_coord.x - instance_coord.y * instance_coord.y));
        pp = (vec4(pp.xyz, 1) * rotationMatrix(rotation_axis, frag_time * cloud_rotation_speed)).xyz;
        pp.x /= 3.0;
        vec3 point = vec3(terrain_seed);
        point.z += swirly_speed * frag_time;
        bool has_clouds = (cnoise(point + pp * swishiness) + 1.0) / 2.0 < cloudiness;
        if (has_clouds) {
            out_color = vec4(cloud_colors[index].rgb, 1.0);
        }
        else if (dist > planet_radius) {
          discard;
        }
    }
    else {
      discard;
    }
}