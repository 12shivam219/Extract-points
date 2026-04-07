#!/usr/bin/env python
"""Test with actual job description"""

from utils.gemini_points_generator import GeminiPointsGenerator

print("=" * 80)
print("TESTING: Backend Developer GoLang/WASM Role")
print("=" * 80)
print()

# Initialize
gen = GeminiPointsGenerator()

# Actual job description from user
job_description = """
Role - Backend Developer - GoLang/WASM (remote)

GoLang 
WebAssembly (WASM) 
APIs supporting React-based front-end applications 
Real-time collaboration services and platform performance optimization 

Design and develop scalable backend services and APIs using GoLang and modern service frameworks to support platform functionality and real-time system operations. 
Support backend services powering and core platform services across the ecosystem. 
Integrate and support WebAssembly (WASM) modules within backend architectures to enable high-performance processing and advanced application capabilities where applicable. 
Architect and maintain RESTful and GraphQL APIs supporting distributed applications and real-time collaboration features. 
Refactor and modernize legacy backend systems into modular microservices or service-oriented architectures. 
Develop backend infrastructure supporting real-time communication, event processing, and collaborative platform capabilities. 
Optimize system performance through efficient concurrency models, caching strategies, and scalable service design. 
Implement secure service communication, authentication, and data access patterns aligned with enterprise security standards. 
Collaborate closely with UI developers using React and TypeScript to ensure seamless integration between user-facing components and backend services. 
Participate in Agile/Scrum ceremonies, including sprint planning, backlog grooming, code reviews, and deployment activities. 
Troubleshoot and resolve complex backend performance issues, service failures, and integration challenges. 
Contribute to system observability through logging, monitoring, metrics, and performance instrumentation. 

Essential Skills:
5+ years of professional backend software development experience 
Strong hands-on development experience with GoLang 
Experience designing and implementing RESTful APIs and microservices architectures 
Experience working with GraphQL APIs 
Familiarity with Java or Node.js service environments 
Experience integrating or supporting WebAssembly (WASM) modules within backend platforms 
Strong understanding of distributed systems and scalable backend architecture patterns 
Experience with event-driven architectures, messaging systems, or WebSocket-based services 
Familiarity with cloud-native or serverless backend architectures 
Experience using Git, CI/CD pipelines, and automated testing frameworks 
Strong debugging and troubleshooting skills within complex backend environments 
Experience working within Agile/Scrum software development environments 

Preferred Technologies:
GoLang 
WebAssembly (WASM) 
Java backend services 
Node.js service layers 
REST and GraphQL APIs 
WebSockets / real-time messaging frameworks 
Containerization (Docker) 
Cloud platforms such as AWS 
Serverless architecture patterns 
Observability tools (logging, metrics, tracing)
"""

job_title = "Backend Developer - GoLang/WASM"
num_points = 3

print("INPUT:")
print(f"Job Title: {job_title}")
print(f"Points per technology: {num_points}")
print()

try:
    print("🔄 Extracting tech stacks...")
    tech_stacks = gen.extract_tech_stacks(job_description)
    
    print("\n" + "=" * 80)
    print("EXTRACTED TECH STACKS:")
    print("=" * 80)
    for i, tech in enumerate(tech_stacks, 1):
        print(f"  {i}. {tech}")
    print()
    
    print("🔄 Generating resume points...")
    print()
    
    points = gen.generate_points(
        job_description=job_description,
        job_title=job_title,
        tech_stacks=tech_stacks,
        num_points=num_points
    )
    
    print("=" * 80)
    print("GENERATED RESUME POINTS:")
    print("=" * 80)
    print()
    print(points)
    print()
    
    # Save to file
    with open('golang_backend_output.txt', 'w') as f:
        f.write(points)
    
    print("=" * 80)
    print(f"✅ Output saved to: golang_backend_output.txt")
    print(f"✅ Total characters: {len(points)}")
    print(f"✅ Tech stacks covered: {len(tech_stacks)}")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
