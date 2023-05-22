use dotenv::dotenv;
use rusoto_core::Region;
use rusoto_s3::{ListObjectsV2Request, S3Client, S3};
use std::{env, error};
use tokio::io::AsyncReadExt;

use serde_json::Value;
use sqlx::postgres::PgPool;
use sqlx::postgres::PgPoolOptions;

async fn store_json_value(pool: &PgPool, key: &str, json_value: &Value) -> Result<(), sqlx::Error> {
    // Convert JSON value to a serialized string
    let json_string = json_value.to_string();

    // Acquire a connection from the connection pool
    let mut conn = pool.acquire().await?;

    // Insert the JSON value into the database using a parameterized query
    sqlx::query("INSERT INTO experiments (key, metadata) VALUES ($1, $2)")
        .bind(key)
        .bind(json_string)
        .execute(&mut conn)
        .await?;

    Ok(())
}

async fn iterate_keys_in_s3_bucket(
    bucket_name: &str,
    endpoint: &str,
    prefix: &str,
    _pool: &PgPool,
) -> Result<(), Box<dyn std::error::Error>> {
    // Configure the S3 client
    let region = Region::Custom {
        name: "custom-region".to_owned(),
        endpoint: endpoint.to_owned(),
    };
    let client = S3Client::new(region);

    // Create a runtime for executing the asynchronous requests
    // let runtime = Runtime::new()?;

    // Define the request parameters
    let mut request = ListObjectsV2Request::default();
    request.bucket = bucket_name.to_owned();
    request.prefix = Some(prefix.to_owned());

    // Iterate over the S3 bucket keys
    loop {
        let response = client.list_objects_v2(request.clone()).await?;
        if let Some(contents) = response.contents {
            for object in contents {
                if let Some(key) = object.key {
                    println!("Key: {}", key);
                    if key.ends_with(".json") {
                        let get_request = rusoto_s3::GetObjectRequest {
                            bucket: bucket_name.to_owned(),
                            key: key.clone(),
                            ..Default::default()
                        };

                        let get_response = client.get_object(get_request).await?;
                        let body = get_response.body.unwrap();
                        let mut buffer = Vec::new();
                        body.into_async_read().read_to_end(&mut buffer).await?;

                        let json_value: Value = serde_json::from_slice(&buffer)?;
                        println!("Key: {}", key);
                        println!("JSON Value: {:?}", json_value);
                    }
                }
            }
        }

        if !response.is_truncated.unwrap_or(false) {
            break;
        }

        if let Some(token) = response.next_continuation_token {
            request.continuation_token = Some(token);
        } else {
            break;
        }
    }

    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn error::Error>> {
    dotenv().ok();

    let pool = PgPoolOptions::new()
        .connect(&env::var("DATABASE_URL").expect("Unable to connect to database"))
        .await?;

    let bucket_name = "braingeneers";
    let endpoint = "https://s3-west.nrp-nautilus.io";
    let prefix = "archive/2020-01-28";

    iterate_keys_in_s3_bucket(bucket_name, endpoint, prefix, &pool).await?;

    Ok(())
}
