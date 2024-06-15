from states import OperatorSG, WorkerSG, CustomerSG

# TOKEN = '6116372134:AAFvsyCXrrkvrOy_LrWqgJQm3F8gqJwyjZI'
TOKEN = '6525353343:AAHW8JVm3wya_x52NdUXM5lAuBqZX-afgL8'
CHIEF_ID = 1126185431

START_STATES = {
    'operator': OperatorSG.main,
    'worker': WorkerSG.main,
    'customer': CustomerSG.main
}
