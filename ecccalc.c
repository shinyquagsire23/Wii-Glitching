#include <stdint.h>
#include <stdio.h>

#define u8 uint8_t
#define u32 uint32_t

static u8 parity(u8 x)
{
	u8 y = 0;

	while (x) {
		y ^= (x & 1);
		x >>= 1;
	}

	return y;
}

void calc_ecc(u8 *data, u8 *ecc)
{
	u8 a[12][2];
	int i, j;
	u32 a0, a1;
	u8 x;

	memset(a, 0, sizeof a);
	for (i = 0; i < 512; i++) {
		x = data[i];
		for (j = 0; j < 9; j++)
			a[3+j][(i >> j) & 1] ^= x;
	}

	x = a[3][0] ^ a[3][1];
	a[0][0] = x & 0x55;
	a[0][1] = x & 0xaa;
	a[1][0] = x & 0x33;
	a[1][1] = x & 0xcc;
	a[2][0] = x & 0x0f;
	a[2][1] = x & 0xf0;

	for (j = 0; j < 12; j++) {
		a[j][0] = parity(a[j][0]);
		a[j][1] = parity(a[j][1]);
	}

	a0 = a1 = 0;
	for (j = 0; j < 12; j++) {
		a0 |= a[j][0] << j;
		a1 |= a[j][1] << j;
	}

	ecc[0] = a0;
	ecc[1] = a0 >> 8;
	ecc[2] = a1;
	ecc[3] = a1 >> 8;
}

int main(int argc, char** argv)
{
    if (argc < 3)
    {
        printf("Usage: ecccalc <file_in> <file_out>\n");
        return -1;
    }

    char* file_in = argv[1];
    char* file_out = argv[2];
    FILE* f = fopen(file_in, "rb");
    FILE* fout = fopen(file_out, "wb");
    
    if (!f)
    {
        printf("Failed to open file `%s`\n", argv[1]);
        return -1;
    }
    
    if (!fout)
    {
        printf("Failed to open file `%s`\n", argv[2]);
        return -1;
    }
    
    u8* data = malloc(0x21000);
    memset(data, 0, 0x21000);
    size_t fsize = fread(data, 0x21000, 1, f);
    fclose(f);
    
    
    
    for (int pos = 0; pos < 0x20000; pos += 0x800)
    {
        u8 ecc[16];
        for (int i = 0; i < 4; i++)
        {
            
            calc_ecc(&data[pos + 512*i], &ecc[i*4]);
            printf("%02x %02x %02x %02x ", ecc[(i*4)+0], ecc[(i*4)+1], ecc[(i*4)+2], ecc[(i*4)+3]);
        }
        
        printf("\n");
        
        fwrite(&data[pos], 0x800, 1, fout);
        
        u8 tmp[0x30];
        memset(tmp, 0xFF, 0x30);
        fwrite(tmp, 0x30, 1, fout);
        fwrite(ecc, 0x10, 1, fout);
    }
    fclose(fout);
}
