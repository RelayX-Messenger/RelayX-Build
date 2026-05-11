#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Chunker core in C for efficiency.
// Part of Project RelayX.

typedef struct {
    int index;
    char* data;
    size_t len;
} Chunk;

Chunk* chunk_file(const char* path, size_t chunk_size, int* out_count) {
    FILE* f = fopen(path, "rb");
    if (!f) return NULL;

    fseek(f, 0, SEEK_END);
    size_t file_size = ftell(f);
    fseek(f, 0, SEEK_SET);

    int num_chunks = (file_size + chunk_size -1) / chunk_size;

    *out_count = num_chunks;

    Chunk* chunks = malloc(sizeof(Chunk) * num_chunks);

    for (int i = 0; i < num_chunks; i++){
        size_t this_size = chunk_size;
        if (i == num_chunks - 1) this_size = file_size - (i * chunk_size);

        chunks[i].data = malloc(this_size);
        size_t read = fread(chunks[i].data, 1, this_size, f);
        chunks[i].len = read;
        chunks[i].index = i;
    }

    fclose(f);
    return chunks;
}

void free_chunks(Chunk* chunks, int count) {
    for (int i = 0; i< count; i++) {
        free(chunks[i].data);
    }
    free(chunks);
}