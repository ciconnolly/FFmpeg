/* CODE ADDED TO FFMpeg 3/1/2021: THIS IS NOT PART OF THE FFMPEG DISTRIBUTION! */
/* REFER TO motion_est.c TO SEE WHERE BITS ARE INSERTED INTO THE STREAM.       */

/*
 * Bitstream code: This code is used to insert / extract bits from a
 * media carrier for steg purpopses.  It is a convenient carrier for
 * steg.
 *
 * -Chris Connolly
 * 
 * 3/1/2021
 *
 */

#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

// #define BITS_TO_PRINT 1024
#define BITS_TO_PRINT 0

/*
 * This file contains Video Embedding Library (vel) bitstream
 * definitions.  For the moment, it's identical to the jelbs object
 * found in ijel.c
 */

typedef struct velbs {
  /* Ephemeral state for bit stuffing / unstuffing - bs==bitstream */
  int bit;                /* "active" bit counter */
  int nbits;              /* Total number of bits in message */
  int bufsize;            /* Buffer size = maximum number of message + length bytes */
  unsigned int stride;    /* Stride for converting macroblock coords to indices. */
  unsigned char density;  /* MCU density - can be in [1,100] */
  unsigned short msgsize; /* Message size must be < bufsize*/
  unsigned char checksum; /* Header checksum */
  unsigned char *msg;
} velbs;


/*
 * For now, we'll just do raw data with length and whole-packet
 * byte-wise checksum.
 */

void velbs_describe( velbs *obj );
int velbs_reset(velbs *obj);
int velbs_set_bufsize(velbs *obj, int n);
int velbs_set_msgsize(velbs *obj, unsigned short n);
velbs *velbs_create_from_string(unsigned char *msg);
int velbs_copy_message(velbs *dst, char *src, int n);
int velbs_got_length(velbs *obj);
long velbs_get_length(velbs *obj);

velbs *velbs_create(int size);
void velbs_destroy(velbs **obj);
void velbs_free(velbs **obj);


int velbs_get_bit(velbs *obj, int k);
int velbs_set_bit(velbs *obj, int k, int val);

int velbs_get_next_bit(velbs *obj);
int velbs_set_next_bit(velbs *obj, int val);

int velbs_set_density(velbs *obj, int density);
int velbs_get_density(velbs *obj);

int vel_tweak_motion_0(int, int*, int*, int);
int vel_tweak_motion_1(int, int*, int*, int);
int vel_tweak_motion_2(int, int *, int *, int *, int);
