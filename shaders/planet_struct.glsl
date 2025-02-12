#ifndef PLANET_STRUCT_LIB
#define PLANET_STRUCT_LIB
#line 4 0
struct PlanetTerrain {
    float seed;
    float bumpiness;
    float water_level;
    float high_level;
    vec3[2] water_colors;
    vec3[2] low_ground_colors;
    vec3[2] high_ground_colors;
};
struct PlanetAtmosphere {
    float cloudiness;
    float swishiness;
    float height;
    float swirl_speed;
    float rotation_multiplier;
    vec3[2] cloud_colors;
};
struct PlanetPhysics {
    float rotation_speed;
    float radius;
    vec3 rotation_axis;
};
#endif
