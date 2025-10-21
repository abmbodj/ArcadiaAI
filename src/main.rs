// src/main.rs

mod lib; 
use lib::GemInterface; 
use std::process; 

// 🟢 FIX: Use the tokio macro to start an asynchronous runtime.
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let query = "What are the latest events at Arcadia University?";

    // NOTE: AiInterface::new() remains synchronous.
    match GemInterface::AiInterface::new() {
        Ok(ai_interface) => {
            println!("Query: {}", query);
            
            // 🟢 The archie method is now async and must be awaited.
            match ai_interface.archie(query).await { 
                Ok(response) => println!("\nArchieAI Response:\n{}", response),
                Err(e) => eprintln!("\nError during AI generation: {}", e),
            }
        }
        Err(e) => {
            eprintln!("\nError initializing AI Interface: {}", e);
            process::exit(1);
        }
    }

    Ok(())
}