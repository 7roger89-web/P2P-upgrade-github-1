#include <stdio.h>
#include <stdlib.h>

__attribute__((noinline, used))
int score_record(int x) {
    return ((x * 7) + 3) ^ 0x2A;
}

__attribute__((noinline, used))
int feature_gate(int mode, int value) {
    if (mode != 7) {
        return -1;
    }
    return score_record(value) + 11;
}

int main(int argc, char **argv) {
    int value = argc > 1 ? atoi(argv[1]) : 5;
    int out = feature_gate(7, value);
    printf("P2P_REA_CANARY_OK:%d\n", out);
    return out == ((((value * 7) + 3) ^ 0x2A) + 11) ? 0 : 2;
}
