"""
Example of using the System Knowledge Graph API.

This example demonstrates how to:
1. Set up a SystemRecorder
2. Register classes with @class_ decorator
3. Register functions with @event decorator
4. Register Pydantic models with @pydantic_model decorator
5. Store Pydantic instances
6. Track function calls automatically
"""

from pydantic import BaseModel, Field
from kgcore.backend.rdf.rdf_rdflib import RDFLibBackend
from kgcore.model.rdf.rdf_base import RDFBaseModel
from kgcore.system import SystemRecorder, set_default_recorder, class_, event, pydantic_model


# ============================================================================
# Step 1: Set up the SystemRecorder
# ============================================================================

backend = RDFLibBackend()
model = RDFBaseModel()
recorder = SystemRecorder(model=model, backend=backend)

# Set as default so decorators can use it
set_default_recorder(recorder)


# ============================================================================
# Step 2: Register a class with @class_ decorator
# ============================================================================

@class_("A web crawler for extracting data from websites")
class WebCrawler:
    """A simple web crawler class."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.visited = set()
    
    def crawl(self, path: str) -> list[str]:
        """Crawl a specific path and return found URLs."""
        # Simulated crawling
        return [f"{self.base_url}/{path}/page1", f"{self.base_url}/{path}/page2"]


# ============================================================================
# Step 3: Register functions with @event decorator
# ============================================================================

@event(
    description="Process raw data and extract structured information",
    auto_version="hash",  # Automatically version based on function hash
    track_calls=True,    # Track each function call
)
def process_data(data: str) -> dict:
    """
    Process raw data string and extract structured information.
    
    Args:
        data: Raw data string
        
    Returns:
        Dictionary with extracted information
    """
    return {
        "processed": True,
        "length": len(data),
        "words": data.split(),
    }


@event(
    description="Validate data format",
    track_calls=True,
)
def validate_data(data: dict) -> bool:
    """Validate that data has required fields."""
    required = ["processed", "length"]
    return all(key in data for key in required)


# ============================================================================
# Step 4: Register Pydantic models with @pydantic_model decorator
# ============================================================================

@pydantic_model("Represents a document extracted from a web page")
class Document(BaseModel):
    """A document model."""
    
    url: str = Field(description="URL where the document was found")
    title: str = Field(description="Title of the document")
    content: str = Field(description="Main content of the document")
    author: str | None = Field(default=None, description="Author of the document")
    timestamp: str = Field(description="When the document was extracted")


@pydantic_model("Represents a processing job")
class ProcessingJob(BaseModel):
    """A processing job model."""
    
    job_id: str = Field(description="Unique job identifier")
    status: str = Field(description="Current status: pending, running, completed, failed")
    input_data: str = Field(description="Input data to process")
    output_data: dict | None = Field(default=None, description="Processed output data")
    error: str | None = Field(default=None, description="Error message if processing failed")


# ============================================================================
# Step 5: Use the registered classes and functions
# ============================================================================

def main():
    print("=== System Knowledge Graph Example ===\n")
    
    # Create a crawler instance
    crawler = WebCrawler("https://example.com")
    print(f"Created WebCrawler instance: {crawler.base_url}")
    
    # Process some data (this will be tracked automatically)
    raw_data = "This is some sample data to process"
    print(f"\nProcessing data: {raw_data}")
    result = process_data(raw_data)
    print(f"Result: {result}")
    
    # Validate the result (this will also be tracked)
    is_valid = validate_data(result)
    print(f"Validation result: {is_valid}")
    
    # Create and store Pydantic instances
    print("\n=== Creating Pydantic Instances ===")
    
    doc1 = Document(
        url="https://example.com/page1",
        title="Example Page 1",
        content="This is the content of page 1",
        author="John Doe",
        timestamp="2024-01-15T10:00:00Z"
    )
    recorder.store_pydantic_instance(doc1, instance_id="doc-001")
    print(f"Stored document: {doc1.title}")
    
    doc2 = Document(
        url="https://example.com/page2",
        title="Example Page 2",
        content="This is the content of page 2",
        timestamp="2024-01-15T11:00:00Z"
    )
    recorder.store_pydantic_instance(doc2, instance_id="doc-002")
    print(f"Stored document: {doc2.title}")
    
    # Create a processing job
    job = ProcessingJob(
        job_id="job-001",
        status="completed",
        input_data=raw_data,
        output_data=result,
    )
    recorder.store_pydantic_instance(job, instance_id="job-001")
    print(f"Stored job: {job.job_id} ({job.status})")
    
    # Manually register a function call (alternative to decorator)
    print("\n=== Manual Function Call Registration ===")
    run_id = recorder.register_function_call(
        "examples.system_kg_api.custom_function",
        args={"0": "test"},
        kwargs={"option": "value"},
        metadata={"source": "manual"}
    )
    print(f"Registered function call: {run_id}")
    recorder.finish_function_call(run_id, result="success")
    
    # Query the graph
    print("\n=== Querying the Knowledge Graph ===")
    
    # Read back a registered class
    crawler_entity = recorder.kg.read_entity("sys:class:examples.system_kg_api.WebCrawler")
    if crawler_entity:
        print(f"\nWebCrawler class entity:")
        print(f"  ID: {crawler_entity.id}")
        print(f"  Labels: {crawler_entity.labels}")
        for prop in crawler_entity.properties:
            print(f"  {prop.key}: {prop.value}")
    
    # Read back a document instance
    doc_entity = recorder.kg.read_entity("sys:instance:doc-001")
    if doc_entity:
        print(f"\nDocument instance entity:")
        print(f"  ID: {doc_entity.id}")
        print(f"  Labels: {doc_entity.labels}")
    
    # Get neighbors (relations)
    print("\n=== Relations ===")
    neighbors = recorder.kg.get_neighbors(
        entity_id="sys:instance:doc-001",
        predicate="http://kgcore.org/system/IS_INSTANCE_OF"
    )
    print(f"Document doc-001 is instance of:")
    for neighbor in neighbors:
        print(f"  - {neighbor.id}")
    
    # Close the recorder
    recorder.close()
    print("\n=== Example completed ===")


if __name__ == "__main__":
    main()
