#include <stdint.h>

extern uint16_t notes_held_bitmap;
extern uint8_t octave;
extern uint8_t most_recent_note_played;
extern uint8_t notes_played[];
extern uint8_t instrument;

extern void draw_rect_white(unsigned int x, unsigned int y, unsigned int x_end, unsigned int y_end);
extern void write_character(char c, int x, int y, int color); // 0=white, 1=black
extern void write_text(const char* str, int x, int y, int color); // 0=white, 1=black


typedef enum {
    C = 0,
    C_SHARP = 1,
    D = 2,
    D_SHARP = 3,
    E = 4,
    F = 5,
    F_SHARP = 6,
    G = 7,
    G_SHARP = 8,
    A = 9,
    A_SHARP = 11,
    B = 13,
    SAMPLE_1 = 10,
    SAMPLE_2 = 12,
    SAMPLE_3 = 14,
} note_bit_type;

#define NOTE(bit_idx) (0x1 << bit_idx)
#define CHORD(x, y, z) (NOTE(x) | NOTE(y) | NOTE(z))

enum instrument {
    PIANO = 0,
    VIOLIN = 1,
    CLARINET = 2,
    DOG = 3,
    SAMPLE_1_INSTRUMENT = 4,
    SAMPLE_2_INSTRUMENT = 5,
    SAMPLE_3_INSTRUMENT = 6,
};

extern int counter;
extern int seq_i;
extern int state;

const note_bit_type note_sequence[] = {
    G, E, D, C, // C@><
    D, E, G, E, // >@C@
    D, C, D, E, // ><>@
    G, E, G, A, // C@CE
    E, A, G, E, // @EC@
    D, C, G, E, // ><C@
    D, C, D, E, // ><>@
    G, E, D, C, // C@><
    D, E, D, E, // >@>@
    G, E, G, A, // C@CE
    E, A, B, G_SHARP, // @EGD
    F_SHARP, E, // B@
};

#define REST_COUNT 10
#define SEQUENCE_LENGTH sizeof(note_sequence)
#define NOTE_PERIOD 16
#define NOTE_HELD_T 4
#define AUTOPLAY_INSTRUMENT VIOLIN


void __attribute__((target("thumb"))) play_note_sequence_src(){
    if (instrument != AUTOPLAY_INSTRUMENT){
        state = 0x0;
        return;
    }

    int all_3_samples_held = CHORD(SAMPLE_1, SAMPLE_2, SAMPLE_3);

    if (state != 0xed){
        if (!((notes_held_bitmap & all_3_samples_held) ^ all_3_samples_held)){
            counter = 0;
            seq_i = 0;
            state = 0xed;
        }
        else{
            return;
        }
    }

    counter += 1;

    if (counter >= NOTE_PERIOD) {
        seq_i += 1;
        if (seq_i >= (SEQUENCE_LENGTH + REST_COUNT)){
            seq_i = 0;
        }

        counter = 0;
    }
    else if (counter >= (NOTE_PERIOD - NOTE_HELD_T) && seq_i < SEQUENCE_LENGTH) {
        note_bit_type next_note_bit = note_sequence[seq_i];
        notes_held_bitmap |= NOTE(next_note_bit);
    }

    return;
}
