PROGRAM=DM_player.exe

CC=gcc

all: $(PROGRAM)

$(PROGRAM): main.o
	$(CC) $^ -o $@

clean:
	$(RM) *.o $(PROGRAM)
