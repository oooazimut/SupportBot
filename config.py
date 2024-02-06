from states import OperatorSG, WorkerSG, CustomerSG

TOKEN = '6525353343:AAHW8JVm3wya_x52NdUXM5lAuBqZX-afgL8'

START_STATES = {
    'operator': OperatorSG.main,
    'worker': WorkerSG.main,
    'customer': CustomerSG.main
}
