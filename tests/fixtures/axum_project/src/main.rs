use axum::{routing::{get, post}, Router};

async fn health() {}
async fn list_items() {}
async fn create_item() {}
async fn delete_item() {}
async fn show_item() {}
async fn update_item() {}

fn app() -> Router {
    let app = Router::new()
        .route("/health", get(health).head(health),)
        .route("/items", get(list_items).post(create_item).delete(delete_item));
    let app = app
        .route(r#"/items/{id}"#, get(show_item).put(update_item))
        .route("/", get(health));

    app.route(dynamic_path, get(health))
        .route(concat!("/unsupported"), get(health))
        .route("/unsupported-method", any(health))
}

// Router::new().route("/commented-out", get(health))
/*
    Router::new().route("/also-commented-out", post(create_item));
    /* nested comment with .route("/ignored", get(health)) */
*/
const EXAMPLE: &str = r#"Router::new().route("/inside-a-string", get(health))"#;
