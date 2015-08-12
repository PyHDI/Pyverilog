.PHONY: all
all: clean

.PHONY: test
test:
	find . -maxdepth 1 -type d |grep "./" | xargs -I {} make test -C {} 

.PHONY: clean
clean:
	find . -maxdepth 1 -type d |grep "./" | xargs -I {} make clean -C {} 
