// src/lib/GemInterface.rs

use dotenv::dotenv;
use std::env;
use std::error::Error;
use std::fmt;

// Imports needed for the successful version
use gemini_rust::{
    Message, Part, Role,
    client::{Error as ClientError, Gemini},
};

// Required for synchronous calling of the async Gemini client
use futures::executor::block_on;

// Crates for web scraping (HTTP and HTML parsing)
use reqwest::{Client, Error as ReqwestError};
use scraper::{Html, Selector};

// ----------------------------------------------------------------------
// 1. Error Handling Definition (Cleaned up for no conflict)
// ----------------------------------------------------------------------

/// Custom error type to encompass potential issues.
#[derive(Debug)]
pub enum AiInterfaceError {
    Environment(String),
    // 🟢 FIX: Renaming to 'Api' to reflect that it handles all boxed errors from the API side.
    Api(Box<dyn Error + Send + Sync>),
    Request(String), // Changed to String as we can't reliably convert reqwest::Error specifically
    General(String),
}

impl fmt::Display for AiInterfaceError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            AiInterfaceError::Environment(msg) => write!(f, "Environment Error: {}", msg),
            AiInterfaceError::Api(e) => write!(f, "Gemini API Error: {}", e),
            AiInterfaceError::Request(msg) => write!(f, "Request Error: {}", msg),
            AiInterfaceError::General(msg) => write!(f, "General Error: {}", msg),
        }
    }
}

impl Error for AiInterfaceError {}

// 🟢 Generic conversion for all errors satisfying the bounds (includes ClientError and Gemini builder errors)
impl<T: Error + Send + Sync + 'static> From<T> for AiInterfaceError
where
    ClientError: From<T>, // Constraint to errors likely from the Gemini crate
{
    fn from(error: T) -> Self {
        // All boxed errors go into the API variant
        AiInterfaceError::Api(Box::new(error))
    }
}

// 🔴 NOTE: We must remove impl From<reqwest::Error> to resolve the conflict.
// We handle reqwest::Error manually in the function body instead of using the '?' operator.

// ----------------------------------------------------------------------
// 2. AiInterface Struct and Methods
// ----------------------------------------------------------------------

/// The main structure for interacting with the Gemini API and web scraping.
pub struct AiInterface {
    client: Gemini,
    http_client: reqwest::Client,
}

impl AiInterface {
    /// Constructor: Initializes the client and loads environment variables.
    pub fn new() -> Result<Self, AiInterfaceError> {
        dotenv().ok();

        let api_key = env::var("GEMINI_API_KEY").map_err(|_| {
            AiInterfaceError::Environment(
                "GEMINI_API_KEY not found. Check your .env file or environment.".to_string(),
            )
        })?;

        // Uses the '?' operator, handled by the generic From<T> impl.
        let client = Gemini::new(api_key)?;
        let http_client = reqwest::Client::new();
        Ok(AiInterface {
            client,
            http_client,
        })
    }

    /// Generate text based on the given prompt using a Gemini model.
    pub async fn generate_text(&self, prompt: &str) -> Result<String, AiInterfaceError> {
        let message = Message::user(prompt.to_string());
        let messages = vec![message];

        let builder = self
            .client
            .generate_content()
            .with_model_message("gemini-2.5-flash-lite")
            .with_messages(messages);

        // Execute the builder. The '?' operator uses the generic From<T> impl.
        let response = builder.execute().await?;
        let text = response
            .candidates
            .first()
            .and_then(|c| c.content.parts.as_ref())
            .and_then(|parts_vec| parts_vec.first())
            .and_then(|p| match p {
                Part::Text { text, .. } => Some(text.clone()),
                _ => None,
            })
            .unwrap_or_else(|| "The model returned no text.".to_string());

        Ok(text)
    }

    /// Scrape the content of a given website and return it as a string.
    pub async fn scrape_website(&self, url: &str) -> Result<String, AiInterfaceError> {
        // 🟢 FIX: Manual error handling for reqwest since the '?' operator is blocked.
        match self.http_client.get(url).send().await {
            Ok(response) => match response.error_for_status() {
                Ok(clean_response) => {
                    let html_content = match clean_response.text().await {
                        Ok(text) => text,
                        Err(e) => {
                            return Err(AiInterfaceError::Request(format!(
                                "Failed to read response body: {}",
                                e
                            )));
                        }
                    };

                    let document = Html::parse_document(&html_content);

                    let selector = match Selector::parse("body") {
                        Ok(s) => s,
                        Err(_) => {
                            return Err(AiInterfaceError::General(
                                "Failed to parse selector".to_string(),
                            ));
                        }
                    };

                    let text_content: String = document
                        .select(&selector)
                        .flat_map(|element| element.text())
                        .collect::<String>()
                        .trim()
                        .to_string();

                    Ok(text_content)
                }
                Err(e) => Err(AiInterfaceError::Request(format!(
                    "HTTP error status: {}",
                    e
                ))),
            },
            Err(e) => Err(AiInterfaceError::Request(format!(
                "Failed to connect or send request: {}",
                e
            ))),
        }
    }

    /// Generate a response for a query using Arcadia University website content.
    pub async fn archie(&self, query: &str) -> Result<String, AiInterfaceError> {
        let website = self.scrape_website("https://www.arcadia.edu/").await?;
        let events = self.scrape_website("https://www.arcadia.edu/events/?mode=month").await?;
        let about = self.scrape_website("https://www.arcadia.edu/about-arcadia/").await?;

        let prompt = format!(
            "System: You are ArchieAI an AI assistant for Arcadia University. You are here to help students, faculty, and staff with any questions they may have about the university. You were made by Eva Akselrad and Ab.
            Using the following website content, answer the query: {}\n\nWebsite Content:\n{}\n\nEvents Content:\n{}\n\nAbout Content:\n{}",
            query, website, events, about
        );

        self.generate_text(&prompt).await
    }
}
