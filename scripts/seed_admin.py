#!/usr/bin/env python3
"""Create or update the initial admin account in the local users DB.

Usage:
    python scripts/seed_admin.py --password <password> [--username admin] [--email x@y.z] [--role admin]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from users import init_db, create_user, get_user, update_password, update_role


def main():
    parser = argparse.ArgumentParser(description="Seed the initial admin account")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--email", default=None, help="Optional email (for Google login)")
    parser.add_argument("--role", default="admin", help="Role (default: admin)")
    args = parser.parse_args()

    init_db()
    if get_user(args.username):
        update_password(args.username, args.password)
        update_role(args.username, args.role)
        print(f"Updated '{args.username}' (role={args.role})")
    else:
        create_user(args.username, args.email, args.password, args.role)
        print(f"Created '{args.username}' (role={args.role})")


if __name__ == "__main__":
    main()
