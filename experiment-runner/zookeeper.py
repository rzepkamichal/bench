import argparse
from datetime import time
import os
import sys
from time import sleep
from kazoo.client import KazooClient, KazooState
from kazoo.security import make_digest_acl,ACL,Permissions

def add_bookie(zk_client, bookie_address):
    """
    Adds a new Bookie to the ZooKeeper ensemble.

    Args:
        zk_client (KazooClient): The Kazoo client instance.
        bookie_address (str): The address of the Bookie to add (e.g., "localhost:3181").
    """

    bookie_path = f"/bookies/{bookie_address}"    ## todo: path do not work
    if not zk_client.exists(bookie_path):
        try:
            Permissions.ALL
            # Create an ACL allowing all permissions
            acl = [make_digest_acl("test","test",all=True)]
            zk_client.create(bookie_path, value=b"", acl=acl)
            print(f"Successfully added Bookie: {bookie_address}")
        except Exception as e:
            print(f"Error adding Bookie: {e}")
    else:
        print(f"Bookie {bookie_address} already exists in the ensemble.")


def list_bookies(zk_client:KazooClient):
    """
    Lists all existing Bookies in the ZooKeeper ensemble.

    Args:
        zk_client (KazooClient): The Kazoo client instance.
    """

    bookies_path = "/"   ## todo: path do not work
    try:
        children = zk_client.get_children(bookies_path)
        if children:
            print("Existing Bookies:")
            for bookie in children:
                print(f"- {bookie}")
        else:
            print("No Bookies found.")
    except Exception as e:
        print(f"Error listing Bookies: {e.with_traceback()}")


def check_connection_state(state):
    if state == KazooState.LOST:
        print("ZooKeeper connection lost")
    elif state == KazooState.SUSPENDED:
        print("ZooKeeper connection suspended")
    else:
        print("Connected")

def connect_to_zookeeper(zookeeper_hosts):
    try:
        zk_client = KazooClient(zookeeper_hosts)
        zk_client.start()
        zk_client.add_listener(check_connection_state)
        print(zk_client.state)
        if zk_client.state != KazooState.CONNECTED:
            raise ConnectionError("no Connection")

        return zk_client
    except Exception as e:
        print(f"Error connecting to ZooKeeper: {e}")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Kazoo-based Bookie Cluster Management Tool")
    parser.add_argument("action", choices=["add_bookie", "list_bookies"], help="The action to perform")
    parser.add_argument("--zookeeper", required=True, help="The ZooKeeper connection string (e.g., localhost:2181)")
    parser.add_argument("--bookie_address", help="The address of the Bookie to add (required for 'add_bookie' action)")
    parser.add_argument("--username", default="user", help="Username for the digest ACL (optional)")
    parser.add_argument("--password", default="password", help="Password for the digest ACL (optional)")
    args = parser.parse_args()

    # Connect to ZooKeeper
    zk_client = connect_to_zookeeper(args.zookeeper)

    if args.action == "add_bookie":
        if not args.bookie_address:
            parser.error("The bookie_address argument is required for the 'add_bookie' action.")
        add_bookie(zk_client, args.bookie_address, username=args.username, password=args.password)
    elif args.action == "list_bookies":
        list_bookies(zk_client)

    # Close ZooKeeper connection
    zk_client.stop()
    zk_client.close()

if __name__ == "__main__":
    main()