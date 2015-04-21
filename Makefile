all: clean

clean_all: clean clean_snapshots clean_pack

clean:
	#
	#	Удаляем скомпилированные файлы байт-кода питона.
	#
	@find ./ -name "*~" -type f -exec rm -f {} \;
	@find ./ -name "*.pyc" -type f -exec rm -f {} \;
	@find ./ -name "*.pyo" -type f -exec rm -f {} \;
	@find ./ -name __pycache__ -type d -exec rm -rf {} \;

##
## Зададим имя архива с проектом.
##
PACKNAME=$(shell basename `pwd`)

##
## Зададим расширение пакета с проектом.
##
PACKEXTN=tar.bz2

##
## Полное имя архива.
##
FULL_PACK_NAME=$(PACKNAME).$(PACKEXTN)

FILES=$(shell find ./ ! -name *.tar.bz2 ! -name *.pyc ! -name *.pyo -type f )


##
## Упакуем архив если его еще нет. 
## Псевдоним для цели `$(FULL_PACK_NAME)`.
##	
pack: | $(FULL_PACK_NAME)

##
## Упакуем архив если его еще нет.
##	
$(FULL_PACK_NAME):
	#
	#	Создаем архив из исходных кодов проекта и элементов Makefile.
	#
	@tar -cjf $@ $(FILES)

clean_pack:
	#
	# 	Удаляет архив.
	#
	@rm -f $(FULL_PACK_NAME);

##
## По `make repack` Перекуем архив, даже если он есть.
##
repack: clean_pack pack

##
## Полное имя для снимка проекта в текущий момент времени.
## C помощью -$(shell <Команда>) мы можем использовать команды bash.
##
SNAPSHOTPREFF=$(PACKNAME)-5nAp5h0t

SNAPSHOTNAME=$(SNAPSHOTPREFF)-$(shell date "+%Y-%m-%d_%H-%M-%S-%N").$(PACKEXTN)

snapshot:
	#
	# 	Создаем архив со снимком проекта.
	#
	@tar -cjf $(SNAPSHOTNAME) $(FILES)

clean_snapshots:
	#
	#	Удаляем все снимки проекта в папке.
	#
	@rm -f $(SNAPSHOTPREFF)*.$(PACKEXTN);
	
##
## Импровизированный вывод справки.
## Псевдоним для цели `help`.
##
man: help

##
## Импровизированный вывод справки.
## 
help:
	@less README.ru_ru.md

	
.PHONY: all clean install-python2 install-python3 help man
