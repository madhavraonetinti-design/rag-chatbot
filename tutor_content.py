"""Curated C# interview learning content used by the Streamlit tutor."""

from datetime import date


DAILY_CURRICULUM_START_DATE = date(2026, 11, 4)


ROADMAP = [
    ("C# Fundamentals", "Beginner", "Types, variables, control flow, methods, and strings."),
    ("OOP Concepts", "Beginner", "Encapsulation, inheritance, polymorphism, and abstraction."),
    ("Collections and LINQ", "Intermediate", "Generic collections, deferred execution, and query operators."),
    ("Exception Handling", "Beginner", "Exception types, custom exceptions, and resilient code."),
    ("Async Programming", "Intermediate", "Task, async/await, cancellation, and concurrency."),
    ("SQL and Database", "Intermediate", "Relational modeling, SQL, transactions, and query efficiency."),
    ("ASP.NET Core", "Intermediate", "Middleware, dependency injection, configuration, and hosting."),
    ("Web API", "Intermediate", "HTTP semantics, REST, validation, and API versioning."),
    ("Entity Framework Core", "Intermediate", "DbContext, migrations, relationships, and query tracking."),
    ("Real-Time Projects", "Advanced", "Build, test, deploy, observe, and explain a complete application."),
]


DAILY_CURRICULUM = [
    {
        "topic": "C# fundamentals",
        "title": "Use statements and deterministic cleanup",
        "difficulty": "Beginner",
        "minutes": 20,
        "objective": "Explain how `using` and `IDisposable` release resources deterministically.",
        "exercise": "Write a method that opens a StreamReader with a using statement, reads one line, and returns it. Then explain what happens if an exception is thrown while reading.",
        "deliverable": "A short C# example and a 2-3 sentence interview explanation.",
    },
    {
        "topic": "C# fundamentals",
        "title": "Value types, reference types, and copying",
        "difficulty": "Beginner",
        "minutes": 20,
        "objective": "Predict assignment and parameter behavior for structs and classes.",
        "exercise": "Create a small struct and class, assign each to a second variable, mutate a field, and record which value changes.",
        "deliverable": "Two snippets and an explanation of value copying versus shared references.",
    },
    {
        "topic": "OOP Concepts",
        "title": "Encapsulation and invariants",
        "difficulty": "Beginner",
        "minutes": 25,
        "objective": "Design a type that protects its state instead of exposing writable fields.",
        "exercise": "Model a bank account with a private balance, Deposit, and Withdraw methods that reject invalid amounts.",
        "deliverable": "A C# class and one invariant the API guarantees.",
    },
    {
        "topic": "Collections and LINQ",
        "title": "LINQ filtering and deferred execution",
        "difficulty": "Beginner",
        "minutes": 20,
        "objective": "Use Where and Select and explain when a LINQ-to-Objects query runs.",
        "exercise": "Filter a list of orders to paid orders and project their IDs. Enumerate the query twice and explain what is reevaluated.",
        "deliverable": "A LINQ query plus one example where ToList is useful.",
    },
    {
        "topic": "Exception Handling",
        "title": "Exceptions and meaningful recovery",
        "difficulty": "Intermediate",
        "minutes": 25,
        "objective": "Catch exceptions at a useful boundary without hiding failures.",
        "exercise": "Parse an input value safely and distinguish invalid user input from an unexpected system failure.",
        "deliverable": "A short method and the reason for each catch or validation branch.",
    },
    {
        "topic": "Async Programming",
        "title": "Async and await without blocking",
        "difficulty": "Intermediate",
        "minutes": 25,
        "objective": "Describe how an async method yields while awaiting incomplete I/O.",
        "exercise": "Convert a blocking HTTP request into an async method using HttpClient and await.",
        "deliverable": "The method signature and a clear explanation of why async does not mean a new thread.",
    },
    {
        "topic": "Collections and LINQ",
        "title": "Choose the right collection",
        "difficulty": "Intermediate",
        "minutes": 20,
        "objective": "Compare List, HashSet, Dictionary, Queue, and Stack by their use cases.",
        "exercise": "Choose data structures for unique tags, user lookup by ID, and FIFO background work.",
        "deliverable": "The collection choice and expected lookup or insertion complexity for each.",
    },
    {
        "topic": "ASP.NET Core",
        "title": "Dependency injection lifetimes",
        "difficulty": "Intermediate",
        "minutes": 25,
        "objective": "Explain transient, scoped, and singleton services and avoid lifetime mismatches.",
        "exercise": "Choose lifetimes for a stateless formatter, an EF Core DbContext, and an in-memory configuration cache.",
        "deliverable": "Three registrations and one example of a captive dependency bug.",
    },
    {
        "topic": "Web API",
        "title": "REST endpoints and HTTP status codes",
        "difficulty": "Intermediate",
        "minutes": 25,
        "objective": "Design resource-oriented endpoints and return appropriate HTTP responses.",
        "exercise": "Sketch create, get, update, and delete endpoints for a training-course resource.",
        "deliverable": "Routes, verbs, and status codes for success, validation failure, and missing resources.",
    },
    {
        "topic": "Entity Framework Core",
        "title": "EF Core tracking and read queries",
        "difficulty": "Intermediate",
        "minutes": 25,
        "objective": "Explain change tracking and when a no-tracking query is appropriate.",
        "exercise": "Write a read-only query that projects course names and learner counts without materializing full entities.",
        "deliverable": "A LINQ query and a note on projection and AsNoTracking.",
    },
    {
        "topic": "SQL and Database",
        "title": "Indexes and query plans",
        "difficulty": "Intermediate",
        "minutes": 25,
        "objective": "Explain how a database index speeds reads and adds write/storage cost.",
        "exercise": "Choose an index for an orders table frequently filtered by customer ID and ordered by creation time.",
        "deliverable": "A proposed index and one query pattern it helps.",
    },
    {
        "topic": "ASP.NET Core",
        "title": "Middleware request pipeline",
        "difficulty": "Intermediate",
        "minutes": 25,
        "objective": "Describe middleware ordering and short-circuit behavior.",
        "exercise": "Order exception handling, routing, authentication, authorization, and endpoint mapping.",
        "deliverable": "The order and one consequence of putting authentication too late.",
    },
    {
        "topic": "Async Programming",
        "title": "Cancellation tokens and responsive APIs",
        "difficulty": "Advanced",
        "minutes": 25,
        "objective": "Propagate CancellationToken through an asynchronous call chain.",
        "exercise": "Add a cancellation token to a controller action and pass it to an async service and database call.",
        "deliverable": "The method signatures and why cancellation should be cooperative.",
    },
    {
        "topic": "Real-Time Projects",
        "title": "Explain a project using STAR",
        "difficulty": "Advanced",
        "minutes": 20,
        "objective": "Present a real technical decision with context, action, and measurable outcome.",
        "exercise": "Choose a .NET project and explain one difficult issue, the options you considered, and the result.",
        "deliverable": "A 90-second answer with a concrete result and one lesson learned.",
    },
]


QUESTIONS = [
    {
        "level": "Beginner",
        "topic": "C# fundamentals",
        "question": "Which statement best describes a C# interface?",
        "options": [
            "A contract that types can implement",
            "A concrete class that cannot be inherited",
            "A variable stored on the stack",
            "A namespace alias",
        ],
        "answer": 0,
        "explanation": "An interface defines a contract of members that implementing types provide. Modern C# also supports default interface implementations.",
    },
    {
        "level": "Beginner",
        "topic": "C# fundamentals",
        "question": "What does the `var` keyword do in a local variable declaration?",
        "options": [
            "Makes the variable dynamically typed",
            "Asks the compiler to infer a static type from the initializer",
            "Makes the value nullable",
            "Allocates the variable on the heap",
        ],
        "answer": 1,
        "explanation": "`var` is compile-time type inference. The variable remains statically typed and its type is fixed by the initializer.",
    },
    {
        "level": "Beginner",
        "topic": "OOP",
        "question": "Which OOP principle hides internal state and exposes controlled operations?",
        "options": ["Inheritance", "Encapsulation", "Overloading", "Serialization"],
        "answer": 1,
        "explanation": "Encapsulation groups state with behavior and restricts direct access so an object can preserve its invariants.",
    },
    {
        "level": "Beginner",
        "topic": "Collections",
        "question": "Which collection provides key-based lookup with average O(1) access?",
        "options": ["List<T>", "Queue<T>", "Dictionary<TKey, TValue>", "LinkedList<T>"],
        "answer": 2,
        "explanation": "Dictionary uses hashing for average constant-time key lookup, subject to a healthy hash distribution.",
    },
    {
        "level": "Intermediate",
        "topic": "Async programming",
        "question": "What does awaiting a Task normally do when the task is incomplete?",
        "options": [
            "Blocks the current OS thread until completion",
            "Returns control to the caller and resumes the async method later",
            "Starts a new thread for every continuation",
            "Cancels the task",
        ],
        "answer": 1,
        "explanation": "`await` is asynchronous coordination, not a thread-creation command. The method is resumed when the awaited operation completes.",
    },
    {
        "level": "Intermediate",
        "topic": "LINQ",
        "question": "When does a typical LINQ-to-Objects `Where` query execute?",
        "options": [
            "Immediately when `Where` is called",
            "When the sequence is enumerated",
            "Only when compiled in Release mode",
            "When the source collection is created",
        ],
        "answer": 1,
        "explanation": "LINQ-to-Objects operators such as `Where` generally use deferred execution; enumeration triggers the predicate evaluations.",
    },
    {
        "level": "Intermediate",
        "topic": "ASP.NET Core",
        "question": "What is the primary purpose of middleware in ASP.NET Core?",
        "options": [
            "To define database tables",
            "To form an ordered request/response processing pipeline",
            "To replace dependency injection",
            "To generate C# assemblies at runtime",
        ],
        "answer": 1,
        "explanation": "Middleware components run in order for HTTP requests and responses, and can call the next component or short-circuit the pipeline.",
    },
    {
        "level": "Intermediate",
        "topic": "Entity Framework Core",
        "question": "What does `AsNoTracking()` primarily change for a read-only EF Core query?",
        "options": [
            "Disables SQL parameterization",
            "Avoids tracking returned entities in the change tracker",
            "Runs the query on another thread",
            "Automatically caches results forever",
        ],
        "answer": 1,
        "explanation": "No-tracking queries avoid change-tracker setup for returned entities, often reducing overhead for read-only results.",
    },
    {
        "level": "Advanced",
        "topic": "Async programming",
        "question": "A service starts several independent I/O-bound tasks. Which approach waits for all of them efficiently?",
        "options": [
            "Await each task before starting the next",
            "Use `Task.WhenAll` on the started tasks",
            "Wrap each task in `Task.Run` by default",
            "Call `.Result` on every task",
        ],
        "answer": 1,
        "explanation": "Start the independent asynchronous operations, then await `Task.WhenAll`. Avoid blocking calls such as `.Result`, which can block threads and cause deadlocks in some contexts.",
    },
    {
        "level": "Advanced",
        "topic": "Web API",
        "question": "Which HTTP status code is the most suitable response after successfully creating a resource?",
        "options": ["200 OK", "201 Created", "204 No Content", "304 Not Modified"],
        "answer": 1,
        "explanation": "201 Created communicates successful resource creation. An API commonly includes a Location header identifying the new resource.",
    },
    {
        "level": "Advanced",
        "topic": "System design",
        "question": "A slow downstream dependency is causing request queues to grow. Which resilience pattern limits concurrent calls to it?",
        "options": ["Circuit breaker only", "Bulkhead", "Repository", "Singleton"],
        "answer": 1,
        "explanation": "A bulkhead isolates capacity and limits concurrency so one failing dependency cannot exhaust all request resources. A circuit breaker complements it by stopping calls after repeated failures.",
    },
    {
        "level": "Advanced",
        "topic": "C# fundamentals",
        "question": "Why should a mutable reference type generally avoid being used as a dictionary key?",
        "options": [
            "Dictionaries cannot store references",
            "Changing equality/hash data after insertion can make lookup inconsistent",
            "The key is automatically copied on every read",
            "The dictionary converts keys to strings",
        ],
        "answer": 1,
        "explanation": "Dictionary lookup depends on a key's equality and hash code. If fields used by those methods change after insertion, the key can become unreachable in its original bucket.",
    },
]


CODING_CHALLENGES = {
    "Palindrome check": {
        "difficulty": "Easy",
        "description": "Implement `IsPalindrome`. Return true when the input reads the same forward and backward, ignoring letter case. Empty strings and one-character strings are palindromes.",
        "starter": "public class Solution\n{\n    public bool IsPalindrome(string text)\n    {\n        // TODO: implement this method\n        return false;\n    }\n}",
        "harness": """public static class Program
{
    public static void Main()
    {
        var solution = new Solution();
        Check(solution.IsPalindrome("Level"), true, "mixed-case palindrome");
        Check(solution.IsPalindrome("dotnet"), false, "non-palindrome");
        Check(solution.IsPalindrome(""), true, "empty string");
    }

    private static void Check(bool actual, bool expected, string name)
    {
        if (actual != expected) throw new Exception($"FAIL {name}: expected {expected}, got {actual}");
        Console.WriteLine($"PASS {name}");
    }
}
""",
    },
    "Find the second largest": {
        "difficulty": "Medium",
        "description": "Implement `SecondLargest` to return the second-largest distinct integer. Throw `InvalidOperationException` if there are fewer than two distinct values.",
        "starter": "using System;\n\npublic class Solution\n{\n    public int SecondLargest(int[] values)\n    {\n        // TODO: implement this method\n        throw new InvalidOperationException();\n    }\n}",
        "harness": """public static class Program
{
    public static void Main()
    {
        var solution = new Solution();
        Check(solution.SecondLargest(new[] { 4, 1, 7, 7, 3 }), 4, "duplicates");
        Check(solution.SecondLargest(new[] { -5, -2, -9 }), -5, "negative values");
    }

    private static void Check(int actual, int expected, string name)
    {
        if (actual != expected) throw new Exception($"FAIL {name}: expected {expected}, got {actual}");
        Console.WriteLine($"PASS {name}");
    }
}
""",
    },
}