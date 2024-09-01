# Para poder trabajar con el compose
import sys
import yaml


def create_clients(file, clients):
    with open(file, 'r') as docker_compose:
        data = yaml.safe_load(docker_compose)

    for i in range(1, clients + 1):
        client = {
            f'client{i}': {
                'container_name': f'client{i}',
                'image': 'client:latest',
                'entrypoint': '/client',
                'environment': [
                    f'CLI_ID={i}',
                    'CLI_LOG_LEVEL=DEBUG'
                ],
                'networks': [
                    'testing_net'
                ],
                'depends_on': [
                    'server'
                ],
                'volumes': [
                    './client/config.yaml:/config.yaml'
                ]

            }
        }
        data['services'].update(client)

    with open(file, 'w') as docker_compose:
        yaml.safe_dump(data, docker_compose, default_flow_style=False)

def create_server(file, n):
    with open(file, 'r') as docker_compose:
        data = yaml.safe_load(docker_compose)

    server = {
        f'server': {
            'container_name': 'server',
            'image': 'server:latest',
            'entrypoint': 'python3 /main.py',
            'environment': [
                'PYTHONUNBUFFERED=1',
                'LOGGING_LEVEL=DEBUG',
                'CLIENTS={n}'
            ],
            'networks': [
                'testing_net'
            ],
            'volumes': [
                './server/config.ini:/config.ini'
            ]
        }
    }

    with open(file, 'w') as docker_compose:
        yaml.safe_dump(data, docker_compose, default_flow_style=False)

if __name__ == '__main__':
    file = sys.argv[1]
    clients = int(sys.argv[2])

    if clients <= 0:
        print("Clients cannot be 0")
        sys.exit(1)

    create_clients(file, clients)
    create_server(file, clients)
