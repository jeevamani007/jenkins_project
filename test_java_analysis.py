import re

# Copy paste the function from demo.py since we can't easily import from it if it has global deps not installed in this env or if structure is complex
# deeper integration test would read from demo.py but this is a unit test of the logic.

def analyze_java_code(code: str):
    """
    Analyze Java code using Regex patterns (since AST is Python specific)
    """
    stats = {
        "functions": 0, 
        "variables": 0, 
        "classes": 0, 
        "imports": 0, 
        "lines": 0, 
        "complexity": 0, 
        "FOR": 0, 
        "database": [], 
        'database_name': [], 
        'time_complexity': 'O(1)',
        'file_bytes': '',
        'function_details': []
    }
    
    try:
        # Basic stats
        stats["lines"] = len(code.splitlines())
        
        # Classes: class ClassName
        stats["classes"] = len(re.findall(r'\bclass\s+\w+', code))
        
        # Methods: simplified regex for method detection
        method_pattern = r'(public|protected|private|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\) *(\{?|[^;])'
        matches = re.findall(method_pattern, code)
        stats["functions"] = len(matches)
        
        # Capture function details (approximate)
        for match in matches:
            stats['function_details'].append({
                "name": match[1],
                "args": [],  
                "docstring": "",
                "line_start": 0, 
                "line_end": 0
            })
            
        # Variables (approximate)
        stats["variables"] = len(re.findall(r'\b(int|String|boolean|double|float|long|char|List|Map|Set)\s+\w+', code))
        
        # Imports
        stats["imports"] = len(re.findall(r'import\s+[\w\.]+', code))
        
        # Loops
        stats["FOR"] = len(re.findall(r'\bfor\s*\(', code)) + len(re.findall(r'\bwhile\s*\(', code))
        
        # DB Connections
        if "DriverManager.getConnection" in code or "DataSource" in code:
            stats["database"].append("JDBC")
            
        if "EntityManager" in code or "@Entity" in code:
             stats["database"].append("JPA/Hibernate")

        # DB Name (simple heuristic)
        db_match = re.search(r'jdbc:[\w]+://[^/]+/(\w+)', code)
        if db_match:
            stats['database_name'].append(db_match.group(1))

        # Complexity Estimation
        if re.search(r'for\s*\(.*for\s*\(.*for\s*\(', code, re.DOTALL):
            stats['time_complexity'] = "O(n³)"
        elif re.search(r'for\s*\(.*for\s*\(', code, re.DOTALL):
            stats['time_complexity'] = "O(n²)"
        elif stats["FOR"] > 0:
            stats['time_complexity'] = "O(n)"
        else:
             stats['time_complexity'] = "O(1)"
             
    except Exception as e:
        print(f"Error analyzing Java code: {e}")
        
    return stats

# Test 1: Simple Java Class
java_code_1 = """
import java.util.List;

public class Employee {
    private int id;
    private String name;

    public Employee(int id, String name) {
        this.id = id;
        this.name = name;
    }

    public void display() {
        System.out.println("Name: " + name);
    }
    
    public int getId() {
        return id;
    }
}
"""

analysis1 = analyze_java_code(java_code_1)
print(f"Test 1 - Classes: {analysis1['classes']} (Expect 1)")
print(f"Test 1 - Functions: {analysis1['functions']} (Expect ~3: Constructor, display, getId)")
print(f"Test 1 - Variables: {analysis1['variables']} (Expect >= 2)")


# Test 2: Database and Loops
java_code_2 = """
import java.sql.DriverManager;
import java.sql.Connection;

public class DBConnection {
    public void connect() {
        String url = "jdbc:mysql://localhost:3306/mydb";
        Connection conn = DriverManager.getConnection(url, "user", "pass");
        
        for (int i = 0; i < 10; i++) {
            for (int j = 0; j < 10; j++) {
                System.out.println(i * j);
            }
        }
    }
}
"""

analysis2 = analyze_java_code(java_code_2)
print(f"Test 2 - Database: {analysis2['database']} (Expect ['JDBC'])")
print(f"Test 2 - DB Name: {analysis2['database_name']} (Expect ['mydb'])")
print(f"Test 2 - Complexity: {analysis2['time_complexity']} (Expect 'O(n²)')")
print(f"Test 2 - Classes: {analysis2['classes']} (Expect 1)")
