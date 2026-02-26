package authz

default allow := false

# Debug rule to see full input context
debug_input := input

allow if {
    input.user == "admin"
}

allow if {
    input.action == "read"
    input.user != ""
}

allow if {
    input.action == "write"
    input.user == "alice"
    input.resource == "data"
}

allow if {
    input.action == "delete"
    input.user == "admin"
}

allow if {
    input.action == "read"
    input.user == "bob"
    input.resource == "reports"
}

# IP-based access control (example)
allow if {
    input.action == "admin"
    input.user == "admin"
    net.cidr_contains("192.168.1.0/24", input.source_ip)
}

# Resource ownership check (example)
allow if {
    input.action == "write"
    input.user == input.resource_owner
}

# Simple rate limiting check (example)
allow if {
    input.action == "api_call"
    input.user == "user"
    input.request_count < 100
}
