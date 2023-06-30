import pandas as pd
from ipaddress import IPv4Network, IPv4Interface
from collections import Counter

code_version = "4.29.3M"
ip_address_mgnt = list(IPv4Network('192.168.1.0/24').hosts())

forms = [{'site':'Rectangle Container', 'leaf':'TerminatorBlock', 'spine':'Preparation','other':'Database', 'line':'Line'}] 
forms_used = ['Rectangle Container', 'TerminatorBlock', 'Preparation','Database', 'Line', 'Document', 'Page', 'Group 1']
forms_nodes = ['TerminatorBlock', 'Preparation','Database']

def check_form_used (df):
    for i, row in df.iterrows():
        if row['Name'] not in forms_used:
            print(f"Forms errors : {row['Name']} is not used")
            exit()

def find_nodes(df):
    nodes = {}
    nodes_container_lab = []
    nodes_container_lab.append("  "*1 + f"nodes:")
    for i, row in df.iterrows():
        if  row['Name'] in forms_nodes:
            nodes.update({row['Id']:{"name":row['Name'], "legend":row['Text Area 1']}})
            nodes_container_lab.append("  "*2 + f"{row['Text Area 1']}:")
            nodes_container_lab.append("  "*3 + f"kind: ceos")
    return [nodes,nodes_container_lab]

def find_links(df,nodes):
    links_container_lab = []
    links = []
    links_container_lab.append("  "*1 +f"links:")
    nodes_ports = {}
    [nodes_ports.update({value["legend"]:0}) for key,value in nodes.items()]
    for i, row in df.iterrows():
        if  row['Name'] == "Line":
            nodes_ports[nodes[int(row['Line Source'])]['legend']] += 1
            nodes_ports[nodes[int(row['Line Destination'])]['legend']] += 1
            node_port_source = nodes_ports[nodes[int(row['Line Source'])]['legend']]
            node_port_destination = nodes_ports[nodes[int(row['Line Destination'])]['legend']]
            links_container_lab.append("  "*2 +f"- endpoints:['{nodes[int(row['Line Source'])]['legend']}:eth{node_port_source}', '{nodes[int(row['Line Destination'])]['legend']}:eth{node_port_destination}']")
            links.append(f"{nodes[int(row['Line Source'])]['legend']}:eth{node_port_source}, {nodes[int(row['Line Destination'])]['legend']}:eth{node_port_destination} ")
    return [links_container_lab,links]

def structure_container_lab(result_nodes_links):
    structure = []
    structure.append("name:lab")
    structure.append("topology:")
    structure.append("  " * 1 + "kinds:")
    structure.append("  " * 2 + "ceos")
    structure.append("  " * 3 + f"image: arista/ceos:{code_version}")
    [structure.append(i) for i in result_nodes_links]
    
    file_write(structure,"container_lab.yml")


def structure_ACT(result_nodes, result_links):
    structure = []
    structure.append('veos:')
    structure.append("  " * 1 + "username: cvpadmin")
    structure.append("  " * 1 + "password: arista123")
    structure.append("  " * 1 + "username: cvpadmin")
    structure.append("  " * 1 + f"version: {code_version}")
  
    structure.append('generic:')
    structure.append("  " * 1 + "username: cvpadmin")
    structure.append("  " * 1 + "password: arista123")
    structure.append("  " * 1 + "version: Rocky-8.5")

    structure.append('cvp:')
    structure.append("  " * 1 + "username: root")
    structure.append("  " * 1 + "password: cvproot")
    structure.append("  " * 1 + "version: 2023.1.0")
    structure.append("  " * 1 + "instance: singlenode")

    structure.append('nodes:')
    ipCounter = 0
    for key,value in result_nodes.items():
        ipCounter += 1
        structure.append("  " * 1 + f"- {value['legend']}:")
        structure.append("  " * 3 + f'ip_addr: {ip_address_mgnt[ipCounter]}')
        structure.append("  " * 3 + f'node_type: veos')
        structure.append("  " * 3 + f'version: {code_version}')
        structure.append("  " * 3 + f'neighbors:')
        for link in result_links:
            if value['legend'] in link:
                if link.find(value['legend']) == 0 :
                    neighbor_device = ((link.split(',')[1]).split(':')[0]).strip()
                    neighbor_port = ((link.split(',')[1]).split(':')[1]).strip()
                    port = ((link.split(',')[0]).split(':')[1]).strip()
                else:
                    neighbor_device = ((link.split(',')[0]).split(':')[0]).strip()
                    neighbor_port = ((link.split(',')[0]).split(':')[1]).strip()
                    port = ((link.split(',')[1]).split(':')[1]).strip()
                structure.append("  " * 4 + f'- neighborDevice: {neighbor_device}')
                structure.append("  " * 5 + f'neighborPort: {neighbor_port.replace("eth","Ethernet")}')
                structure.append("  " * 5 + f'port: {port.replace("eth","Ethernet")}')
        structure.append("  "* 3 + f'ports: []')
    
    ipCounter += 1
    structure.append("  " * 1 + f"- cvp:")
    structure.append("  " * 3 + f'ip_addr: {ip_address_mgnt[ipCounter]}')
    structure.append("  " * 3 + f'node_type: cvp')

    ipCounter += 1
    structure.append("  " * 1 + f"- devopps:")
    structure.append("  " * 3 + f'ip_addr: {ip_address_mgnt[ipCounter]}')
    structure.append("  " * 3 + f'node_type: generic')
    
    file_write(structure,"ACT_lab.yml")


def file_write(structure, file_name):
    file= open(file_name,"w")
    for line in structure:
        file.write(line + "\n")
    file.close()

if __name__ == "__main__":
    df = pd.read_csv ('Test calibration.csv', usecols=['Id','Name', 'Contained By', 'Line Source', 'Line Destination', 'Text Area 1'])
    check_form_used(df)
    result_nodes = find_nodes(df)
    result_links = find_links(df,result_nodes[0])
    structure_container_lab(result_nodes[1]+result_links[0])
    structure_ACT(result_nodes[0], result_links[1])
    
