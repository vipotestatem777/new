workspace "Synthetic order system" "Original reference; no remote themes or includes" {
    model {
        customer = person "Customer"
        orders = softwareSystem "Order service" {
            web = container "Web application" "Customer interface" "Browser"
            api = container "Order API" "Owns order contracts" "Application"
            queue = container "Event queue" "At-least-once delivery" "Message broker"
            worker = container "Order worker" "Idempotent event handling" "Application"
            store = container "Order store" "Owned order records" "Database"
        }
        customer -> orders "Places orders"
        customer -> web "Uses"
        web -> api "Requests orders" "HTTPS"
        api -> store "Reads and writes"
        api -> queue "Publishes order events"
        queue -> worker "Delivers events"
        worker -> store "Applies idempotent updates"
    }
    views {
        systemContext orders "Context" {
            include *
            autoLayout lr
        }
        container orders "Containers" {
            include *
            autoLayout lr
        }
    }
}
