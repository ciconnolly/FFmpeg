/* CODE ADDED TO FFMpeg 3/1/2021: THIS IS NOT PART OF THE FFMPEG DISTRIBUTION! */
/* REFER TO motion_est.c TO SEE WHERE BITS ARE INSERTED INTO THE STREAM.       */


#include "velbs.h"

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

/*
 * The velbs struct is ASSUMED to hold an integral number of 8-bit
 * bytes.  That is, we are not allowed to encode partial bytes.
 * Hence, nbits should always be 8 * nbytes.  Might be a little
 * redundant, but it's easier to inspect.
 */

void velbs_describe( velbs *obj ) {
  /* Print a description of the bitstream */
  printf("bit:        %d\n", obj->bit);
  printf("nbits:      %d\n", obj->nbits);
  printf("bufsize:    %d\n", obj->bufsize);
  printf("density:    %d\n", obj->density);
  printf("msgsize:    %d\n", obj->msgsize);
  printf("checksum:   %x\n", obj->checksum);
  //  printf("message:    %s\n", obj->message);
}


/* bitstream operations: This API supports bitwise stuffing and
 *  unstuffing into MCUs. */




int velbs_reset(velbs *obj) {
  /* Reset the bit stream to its initial state */
  obj->bit = 0;
  obj->nbits = (obj->msgsize + sizeof(obj->density) + sizeof(obj->msgsize) + sizeof(obj->checksum) ) * 8;
  return 0;
}



int velbs_set_bufsize(velbs *obj, int n) {
  /* For "empty" bit streams, set length explicitly. */
  obj->bufsize = n;
  velbs_reset( obj );
  return obj->nbits;
}

int velbs_set_msgsize(velbs *obj, unsigned short n) {
  /* For "empty" bit streams, set length explicitly. */
  obj->msgsize = n;
  velbs_reset( obj );
  return obj->nbits;
}


static void velbs_compute_checksum(velbs *bs) {
  unsigned char b = bs->density;
  unsigned char *len = (unsigned char*) &(bs->msgsize);
  b ^= len[0];
  b ^= len[1];
  bs->checksum = b;
}


static int velbs_validate_checksum(velbs *bs) {
  unsigned char b = bs->density;
  unsigned char *len = (unsigned char*) &(bs->msgsize);
  b ^= len[0];
  b ^= len[1];
  if (bs->checksum == b) {
    printf("Checksums match: %d == %d.\n", b, bs->checksum);
    return 1;
  } else {
    printf("Checksum mismatch: %d vs. %d.\n", b, bs->checksum);
    return 0;
  }
}

/* Some confusion here, in that we depend on msg being a
 * zero-terminated string, but empty buffers can also be used.  It's
 * probably not good to depend on a null-terminated msg arg:
 */

velbs *velbs_create_from_string(unsigned char *msg) {
  /* Creates and returns a bit stream object from a given string. */
  velbs* obj = (velbs*) calloc(1, sizeof(velbs));

  obj->msgsize = strlen( (const char*) msg);
  obj->bufsize = obj->msgsize;
  obj->msg = msg;
  velbs_reset(obj);
  return obj;
}


int velbs_copy_message(velbs *dst, char *src, int n) {
  if (memmove(dst->msg, src, (unsigned int) n)) return n;
  else return 0;
}

velbs *velbs_create(int size) {
  /* Creates and returns a bit stream object from a requested message size. */
  velbs* obj = (velbs*) calloc(1, sizeof(velbs));

  obj->msgsize = size;
  obj->bufsize = 2*size + 1;  // Provide ample space just in case.
  obj->msg = calloc(1, (unsigned int) obj->bufsize);
  velbs_reset(obj);
  return obj;
}


/* Companion to velbs_create(n): Assumes that the message buffer has
 * been allocated by the velbs API. */
void velbs_destroy(velbs **obj) {
  if ( *obj ) {
    if ( (*obj)->msg ) free((*obj)->msg);
    free(*obj);
    *obj = NULL;
  }
}


int velbs_got_length(velbs *obj) {
  return( (unsigned int) obj->bit >= 8 * (sizeof(obj->density) + sizeof(obj->msgsize) + sizeof(obj->checksum)) );
}

/* When length is embedded, it is the first long in the bitstream: */
long velbs_get_length(velbs *obj) {
  return (long) (obj->msgsize);
}


int velbs_get_density(velbs *obj) {
  return (int) obj->density;
}


int velbs_set_density(velbs *obj, int density) {
  obj->density = (unsigned char) density;
  return density;
}


void velbs_free(velbs **obj) {
  /* Free the bitstream object */
  free(*obj);
  *obj = NULL;
}


/* Would be good to do some sanity checking in these operations: */

int velbs_get_bit(velbs *obj, int k) {
  int offset = (sizeof(obj->density) + sizeof(obj->msgsize) + sizeof(obj->checksum) );
  unsigned char *len = (unsigned char*) &(obj->msgsize);
  unsigned char byte;
  /* Extract the k-th bit from the bitstream.  First compute
   * offsets: */
  int bit_in_byte = k % 8;
  int byte_in_msg = (k / 8) - offset;

  /* Mask out and shift to return either 1 or 0: */
  unsigned char mask = (1 << bit_in_byte);

  /* We are going to encode density and message length.  This logic is
     now agnostic about packing in the struct, so should work modulo
     endian-ness: */
  if (k < 8)       byte = obj->density; // This is in the first byte: density
  else if (k < 16) byte = len[0];
  else if (k < 24) byte = len[1];
  else if (k < 32) byte = obj->checksum;
  else             byte = obj->msg[byte_in_msg];

  int val = (mask & byte) >> bit_in_byte;

  //  if (k == 24) printf("Length = %d\n", obj->msgsize);
  if (k < BITS_TO_PRINT) printf("%d", val);

  return val;
}
  


int velbs_set_bit(velbs *obj, int k, int val) {
  int offset =  (sizeof(obj->density) + sizeof(obj->msgsize) + sizeof(obj->checksum) );
  unsigned char *len = (unsigned char*) &(obj->msgsize);
  unsigned char byte;
  /* Set the k-th bit from the bitstream to the value 'val'.  First
   * compute offsets: */
  int bit_in_byte = k % 8;
  int byte_in_msg = (k / 8) - offset;

  /* Then mask in the bit: */
  unsigned char vmask = (val << bit_in_byte);
  unsigned char mask = 0xFF & ~(1 << bit_in_byte);
  /* Mask is now an unsigned char with the 'val' bit in the appropriate bit position */
  
  /* Extract the appropriate byte: */
  if (k < 8)       byte = obj->density; // This is in the first byte: density
  else if (k < 16) byte = len[0];
  else if (k < 24) byte = len[1];
  else if (k < 32) byte = obj->checksum;
  else             byte = obj->msg[byte_in_msg];

  /* Complement the mask, ANDing it with the byte.  Then or in the 'val' bit: */
  unsigned char new = (byte & mask) | vmask;

  /* Set the altered byte: */
  if (k < 8)       obj->density = new; // This is in the first byte: density
  else if (k < 16) len[0] = new;
  else if (k < 24) len[1] = new;
  else if (k < 32) obj->checksum = new;
  else             obj->msg[byte_in_msg] = new;

  //  if (k == 24) printf("Length = %d\n", obj->msgsize);
  if (k < BITS_TO_PRINT) printf("%d", val);

  return val;
}




int velbs_get_next_bit(velbs *obj) {
  /* Get the next bit and advance the bit counter: */
  int result;
  if (obj->bit >= obj->nbits) return -1;
  else {
    result = velbs_get_bit(obj, obj->bit);
    obj->bit++;
    return result;
  }
}


int velbs_set_next_bit(velbs *obj, int val) {
  /* Set the next bit to 'val' and advance the bit counter: */
  int result;
  if (obj->bit >= obj->nbits) return -1;
  else {
    result = velbs_set_bit(obj, obj->bit, val);
    obj->bit++;
    return result;
  }
}

