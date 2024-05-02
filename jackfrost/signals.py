from django.dispatch import Signal

build_started = Signal()

build_finished = Signal()

reader_started = Signal()

reader_finished = Signal()

read_page = Signal()

write_page = Signal()

writer_started = Signal()

writer_finished = Signal()
