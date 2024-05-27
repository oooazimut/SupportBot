from states import OperatorSG, WorkerSG, CustomerSG

TOKEN = '6116372134:AAFvsyCXrrkvrOy_LrWqgJQm3F8gqJwyjZI'

START_STATES = {
    'operator': OperatorSG.main,
    'worker': WorkerSG.main,
    'customer': CustomerSG.main
}
