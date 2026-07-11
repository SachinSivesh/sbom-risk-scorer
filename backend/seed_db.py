import os
import uuid
import json
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import backend modules
from app.config import get_settings
from app.models.application import Application
from app.models.sbom import Sbom
from app.models.dependency import Dependency, DependencyEdge
from app.models.vulnerability import Vulnerability
from app.models.maintenance import MaintenanceSignal
from app.models.risk_report import RiskReport
from app.models.ai_report import AIReport

settings = get_settings()
sync_engine = create_engine(settings.SYNC_DATABASE_URL)
SyncSession = sessionmaker(bind=sync_engine)

def seed():
    session = SyncSession()
    print("Clearing existing database tables...")
    try:
        session.query(AIReport).delete()
        session.query(RiskReport).delete()
        session.query(DependencyEdge).delete()
        session.query(Dependency).delete()
        session.query(Sbom).delete()
        session.query(Application).delete()
        session.commit()
        print("Database cleared successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error clearing database: {e}")
        return

    # Ensure storage directory exists
    os.makedirs(settings.SBOM_STORAGE_PATH, exist_ok=True)

    # 1. Tech Stack Dependency Tree Definitions
    # Node.js Tree Definition (20-40 nodes)
    nodejs_deps = [
        {"name": "express", "version": "4.17.1", "license": "MIT", "is_direct": True, "repo": "https://github.com/expressjs/express", "maint_score": 80, "status": "OK"},
        {"name": "helmet", "version": "5.0.2", "license": "MIT", "is_direct": True, "repo": "https://github.com/helmetjs/helmet", "maint_score": 90, "status": "OK"},
        {"name": "cors", "version": "2.8.5", "license": "MIT", "is_direct": True, "repo": "https://github.com/expressjs/cors", "maint_score": 85, "status": "OK"},
        {"name": "axios", "version": "1.3.4", "license": "MIT", "is_direct": True, "repo": "https://github.com/axios/axios", "maint_score": 45, "status": "INACTIVE"},
        {"name": "jsonwebtoken", "version": "9.0.0", "license": "MIT", "is_direct": True, "repo": "https://github.com/auth0/node-jsonwebtoken", "maint_score": 75, "status": "OK"},
        {"name": "bcrypt", "version": "5.1.0", "license": "BSD-3-Clause", "is_direct": True, "repo": "https://github.com/kelektiv/node.bcrypt.js", "maint_score": 88, "status": "OK"},
        {"name": "dotenv", "version": "16.0.3", "license": "BSD-2-Clause", "is_direct": True, "repo": "https://github.com/motdotla/dotenv", "maint_score": 95, "status": "OK"},
        {"name": "winston", "version": "3.8.2", "license": "MIT", "is_direct": True, "repo": "https://github.com/winstonjs/winston", "maint_score": 70, "status": "OK"},
        {"name": "mongoose", "version": "6.10.0", "license": "MIT", "is_direct": True, "repo": "https://github.com/Automattic/mongoose", "maint_score": 60, "status": "OK"},
        {"name": "compression", "version": "1.7.4", "license": "MIT", "is_direct": True, "repo": "https://github.com/expressjs/compression", "maint_score": 25, "status": "DEPRECATED"},
        
        # Transitive Node.js dependencies
        {"name": "body-parser", "version": "1.19.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/expressjs/body-parser", "maint_score": 70, "status": "OK"},
        {"name": "debug", "version": "4.3.1", "license": "MIT", "is_direct": False, "repo": "https://github.com/debug-js/debug", "maint_score": 75, "status": "OK"},
        {"name": "ms", "version": "2.1.2", "license": "MIT", "is_direct": False, "repo": "https://github.com/vercel/ms", "maint_score": 95, "status": "OK"},
        {"name": "accepts", "version": "1.3.7", "license": "MIT", "is_direct": False, "repo": "https://github.com/jshttp/accepts", "maint_score": 65, "status": "OK"},
        {"name": "mime-types", "version": "2.1.27", "license": "MIT", "is_direct": False, "repo": "https://github.com/jshttp/mime-types", "maint_score": 80, "status": "OK"},
        {"name": "negotiator", "version": "0.6.2", "license": "MIT", "is_direct": False, "repo": "https://github.com/jshttp/negotiator", "maint_score": 50, "status": "OK"},
        {"name": "send", "version": "0.17.1", "license": "MIT", "is_direct": False, "repo": "https://github.com/pillarjs/send", "maint_score": 60, "status": "OK"},
        {"name": "mime", "version": "1.6.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/broofa/mime", "maint_score": 55, "status": "OK"},
        {"name": "etag", "version": "1.8.1", "license": "MIT", "is_direct": False, "repo": "https://github.com/jshttp/etag", "maint_score": 85, "status": "OK"},
        {"name": "follow-redirects", "version": "1.15.2", "license": "MIT", "is_direct": False, "repo": "https://github.com/follow-redirects/follow-redirects", "maint_score": 90, "status": "OK"},
        {"name": "form-data", "version": "4.0.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/form-data/form-data", "maint_score": 70, "status": "OK"},
        {"name": "asynckit", "version": "0.4.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/caolan/asynckit", "maint_score": 10, "status": "ARCHIVED"},
        {"name": "combined-stream", "version": "1.0.8", "license": "MIT", "is_direct": False, "repo": "https://github.com/felixge/node-combined-stream", "maint_score": 40, "status": "OK"},
        {"name": "mime-db", "version": "1.44.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/jshttp/mime-db", "maint_score": 80, "status": "OK"},
        {"name": "mongodb", "version": "4.14.0", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/mongodb/node-mongodb-native", "maint_score": 90, "status": "OK"},
        {"name": "mpath", "version": "0.9.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/aheckmann/mpath", "maint_score": 30, "status": "INACTIVE"},
        {"name": "mquery", "version": "4.0.3", "license": "MIT", "is_direct": False, "repo": "https://github.com/aheckmann/mquery", "maint_score": 35, "status": "INACTIVE"},
        {"name": "kareem", "version": "2.5.1", "license": "MIT", "is_direct": False, "repo": "https://github.com/aheckmann/kareem", "maint_score": 40, "status": "OK"},
        {"name": "safe-buffer", "version": "5.2.1", "license": "MIT", "is_direct": False, "repo": "https://github.com/feross/safe-buffer", "maint_score": 85, "status": "OK"}
    ]
    nodejs_edges = [
        {"from": "express", "to": "body-parser"},
        {"from": "express", "to": "debug"},
        {"from": "express", "to": "accepts"},
        {"from": "express", "to": "send"},
        {"from": "express", "to": "qs"},
        {"from": "accepts", "to": "mime-types"},
        {"from": "accepts", "to": "negotiator"},
        {"from": "mime-types", "to": "mime-db"},
        {"from": "send", "to": "mime"},
        {"from": "send", "to": "etag"},
        {"from": "debug", "to": "ms"},
        {"from": "axios", "to": "follow-redirects"},
        {"from": "axios", "to": "form-data"},
        {"from": "form-data", "to": "asynckit"},
        {"from": "form-data", "to": "combined-stream"},
        {"from": "jsonwebtoken", "to": "ms"},
        {"from": "mongoose", "to": "mongodb"},
        {"from": "mongoose", "to": "mpath"},
        {"from": "mongoose", "to": "mquery"},
        {"from": "mongoose", "to": "kareem"}
    ]

    # Java Tree Definition (30-60 nodes)
    java_deps = [
        {"name": "spring-core", "version": "5.3.20", "license": "Apache-2.0", "is_direct": True, "repo": "https://github.com/spring-projects/spring-framework", "maint_score": 95, "status": "OK"},
        {"name": "spring-web", "version": "5.3.20", "license": "Apache-2.0", "is_direct": True, "repo": "https://github.com/spring-projects/spring-framework", "maint_score": 95, "status": "OK"},
        {"name": "spring-security", "version": "5.7.1", "license": "Apache-2.0", "is_direct": True, "repo": "https://github.com/spring-projects/spring-security", "maint_score": 90, "status": "OK"},
        {"name": "spring-data-jpa", "version": "2.7.0", "license": "Apache-2.0", "is_direct": True, "repo": "https://github.com/spring-projects/spring-data-jpa", "maint_score": 85, "status": "OK"},
        {"name": "jackson-databind", "version": "2.13.3", "license": "Apache-2.0", "is_direct": True, "repo": "https://github.com/FasterXML/jackson-databind", "maint_score": 80, "status": "OK"},
        {"name": "hibernate-core", "version": "5.6.9.Final", "license": "LGPL-2.1-or-later", "is_direct": True, "repo": "https://github.com/hibernate/hibernate-orm", "maint_score": 75, "status": "OK"},
        {"name": "logback-classic", "version": "1.2.11", "license": "EPL-1.0", "is_direct": True, "repo": "https://github.com/qos-ch/logback", "maint_score": 60, "status": "OK"},
        {"name": "log4j-core", "version": "2.17.1", "license": "Apache-2.0", "is_direct": True, "repo": "https://github.com/apache/logging-log4j2", "maint_score": 5, "status": "DEPRECATED"},
        {"name": "commons-io", "version": "2.11.0", "license": "Apache-2.0", "is_direct": True, "repo": "https://github.com/apache/commons-io", "maint_score": 40, "status": "INACTIVE"},
        {"name": "tomcat-embed-core", "version": "9.0.63", "license": "Apache-2.0", "is_direct": True, "repo": "https://github.com/apache/tomcat", "maint_score": 80, "status": "OK"},
        {"name": "hikaricp", "version": "4.0.3", "license": "Apache-2.0", "is_direct": True, "repo": "https://github.com/brettwooldridge/HikariCP", "maint_score": 85, "status": "OK"},
        {"name": "micrometer-core", "version": "1.9.0", "license": "Apache-2.0", "is_direct": True, "repo": "https://github.com/micrometer-metrics/micrometer", "maint_score": 88, "status": "OK"},

        # Transitive Java dependencies
        {"name": "spring-jcl", "version": "5.3.20", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/spring-projects/spring-framework", "maint_score": 95, "status": "OK"},
        {"name": "spring-beans", "version": "5.3.20", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/spring-projects/spring-framework", "maint_score": 95, "status": "OK"},
        {"name": "spring-aop", "version": "5.3.20", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/spring-projects/spring-framework", "maint_score": 95, "status": "OK"},
        {"name": "spring-expression", "version": "5.3.20", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/spring-projects/spring-framework", "maint_score": 95, "status": "OK"},
        {"name": "spring-security-core", "version": "5.7.1", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/spring-projects/spring-security", "maint_score": 90, "status": "OK"},
        {"name": "spring-security-web", "version": "5.7.1", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/spring-projects/spring-security", "maint_score": 90, "status": "OK"},
        {"name": "jackson-annotations", "version": "2.13.3", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/FasterXML/jackson-annotations", "maint_score": 80, "status": "OK"},
        {"name": "jackson-core", "version": "2.13.3", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/FasterXML/jackson-core", "maint_score": 80, "status": "OK"},
        {"name": "jboss-logging", "version": "3.4.3.Final", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/jboss-logging/jboss-logging", "maint_score": 60, "status": "OK"},
        {"name": "classmate", "version": "1.5.1", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/FasterXML/java-classmate", "maint_score": 50, "status": "OK"},
        {"name": "antlr", "version": "2.7.7", "license": "BSD-3-Clause", "is_direct": False, "repo": "https://github.com/antlr/antlr4", "maint_score": 20, "status": "ARCHIVED"},
        {"name": "dom4j", "version": "2.1.3", "license": "BSD-3-Clause", "is_direct": False, "repo": "https://github.com/dom4j/dom4j", "maint_score": 45, "status": "INACTIVE"},
        {"name": "logback-core", "version": "1.2.11", "license": "EPL-1.0", "is_direct": False, "repo": "https://github.com/qos-ch/logback", "maint_score": 60, "status": "OK"},
        {"name": "slf4j-api", "version": "1.7.36", "license": "MIT", "is_direct": False, "repo": "https://github.com/qos-ch/slf4j", "maint_score": 95, "status": "OK"},
        {"name": "log4j-api", "version": "2.17.1", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/apache/logging-log4j2", "maint_score": 5, "status": "DEPRECATED"},
        {"name": "tomcat-annotations-api", "version": "9.0.63", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/apache/tomcat", "maint_score": 80, "status": "OK"}
    ]
    java_edges = [
        {"from": "spring-core", "to": "spring-jcl"},
        {"from": "spring-web", "to": "spring-beans"},
        {"from": "spring-web", "to": "spring-aop"},
        {"from": "spring-web", "to": "spring-core"},
        {"from": "spring-security", "to": "spring-security-core"},
        {"from": "spring-security", "to": "spring-security-web"},
        {"from": "spring-security-web", "to": "spring-expression"},
        {"from": "spring-data-jpa", "to": "spring-beans"},
        {"from": "spring-data-jpa", "to": "spring-core"},
        {"from": "jackson-databind", "to": "jackson-annotations"},
        {"from": "jackson-databind", "to": "jackson-core"},
        {"from": "hibernate-core", "to": "jboss-logging"},
        {"from": "hibernate-core", "to": "classmate"},
        {"from": "hibernate-core", "to": "antlr"},
        {"from": "hibernate-core", "to": "dom4j"},
        {"from": "logback-classic", "to": "logback-core"},
        {"from": "logback-classic", "to": "slf4j-api"},
        {"from": "log4j-core", "to": "log4j-api"},
        {"from": "tomcat-embed-core", "to": "tomcat-annotations-api"}
    ]

    # Python Tree Definition (20-40 nodes)
    python_deps = [
        {"name": "fastapi", "version": "0.95.0", "license": "MIT", "is_direct": True, "repo": "https://github.com/tiangolo/fastapi", "maint_score": 95, "status": "OK"},
        {"name": "starlette", "version": "0.26.1", "license": "BSD-3-Clause", "is_direct": True, "repo": "https://github.com/encode/starlette", "maint_score": 90, "status": "OK"},
        {"name": "pydantic", "version": "1.10.7", "license": "MIT", "is_direct": True, "repo": "https://github.com/pydantic/pydantic", "maint_score": 92, "status": "OK"},
        {"name": "uvicorn", "version": "0.21.1", "license": "BSD-3-Clause", "is_direct": True, "repo": "https://github.com/encode/uvicorn", "maint_score": 85, "status": "OK"},
        {"name": "sqlalchemy", "version": "2.0.7", "license": "MIT", "is_direct": True, "repo": "https://github.com/sqlalchemy/sqlalchemy", "maint_score": 88, "status": "OK"},
        {"name": "requests", "version": "2.28.2", "license": "Apache-2.0", "is_direct": True, "repo": "https://github.com/psf/requests", "maint_score": 75, "status": "OK"},
        {"name": "jinja2", "version": "3.1.2", "license": "BSD-3-Clause", "is_direct": True, "repo": "https://github.com/pallets/jinja", "maint_score": 80, "status": "OK"},
        {"name": "urllib3", "version": "1.26.15", "license": "MIT", "is_direct": True, "repo": "https://github.com/urllib3/urllib3", "maint_score": 85, "status": "OK"},
        {"name": "click", "version": "8.1.3", "license": "BSD-3-Clause", "is_direct": True, "repo": "https://github.com/pallets/click", "maint_score": 78, "status": "OK"},
        {"name": "certifi", "version": "2022.12.7", "license": "MPL-2.0", "is_direct": True, "repo": "https://github.com/certifi/python-certifi", "maint_score": 98, "status": "OK"},

        # Transitives Python dependencies
        {"name": "h11", "version": "0.14.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/python-hyper/h11", "maint_score": 60, "status": "OK"},
        {"name": "websockets", "version": "10.4", "license": "BSD-3-Clause", "is_direct": False, "repo": "https://github.com/aaugustin/websockets", "maint_score": 80, "status": "OK"},
        {"name": "greenlet", "version": "2.0.2", "license": "MIT", "is_direct": False, "repo": "https://github.com/python-greenlet/greenlet", "maint_score": 40, "status": "OK"},
        {"name": "idna", "version": "3.4", "license": "BSD-3-Clause", "is_direct": False, "repo": "https://github.com/kjd/idna", "maint_score": 90, "status": "OK"},
        {"name": "charset-normalizer", "version": "3.1.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/Ousret/charset-normalizer", "maint_score": 85, "status": "OK"},
        {"name": "markupsafe", "version": "2.1.2", "license": "BSD-3-Clause", "is_direct": False, "repo": "https://github.com/pallets/markupsafe", "maint_score": 82, "status": "OK"},
        {"name": "anyio", "version": "3.6.2", "license": "MIT", "is_direct": False, "repo": "https://github.com/agronholm/anyio", "maint_score": 78, "status": "OK"},
        {"name": "sniffio", "version": "1.3.0", "license": "Apache-2.0", "is_direct": False, "repo": "https://github.com/python-attrs/sniffio", "maint_score": 75, "status": "OK"}
    ]
    python_edges = [
        {"from": "fastapi", "to": "starlette"},
        {"from": "fastapi", "to": "pydantic"},
        {"from": "fastapi", "to": "anyio"},
        {"from": "starlette", "to": "anyio"},
        {"from": "anyio", "to": "sniffio"},
        {"from": "uvicorn", "to": "h11"},
        {"from": "uvicorn", "to": "websockets"},
        {"from": "uvicorn", "to": "click"},
        {"from": "sqlalchemy", "to": "greenlet"},
        {"from": "requests", "to": "urllib3"},
        {"from": "requests", "to": "idna"},
        {"from": "requests", "to": "charset-normalizer"},
        {"from": "requests", "to": "certifi"},
        {"from": "jinja2", "to": "markupsafe"}
    ]

    # Go Tree Definition (20-40 nodes)
    go_deps = [
        {"name": "github.com/gin-gonic/gin", "version": "1.8.1", "license": "MIT", "is_direct": True, "repo": "https://github.com/gin-gonic/gin", "maint_score": 94, "status": "OK"},
        {"name": "github.com/go-playground/validator/v10", "version": "10.11.0", "license": "MIT", "is_direct": True, "repo": "https://github.com/go-playground/validator", "maint_score": 88, "status": "OK"},
        {"name": "github.com/golang-jwt/jwt/v5", "version": "5.0.0", "license": "MIT", "is_direct": True, "repo": "https://github.com/golang-jwt/jwt", "maint_score": 85, "status": "OK"},
        {"name": "go.uber.org/zap", "version": "1.24.0", "license": "MIT", "is_direct": True, "repo": "https://github.com/uber-go/zap", "maint_score": 90, "status": "OK"},
        {"name": "gorm.io/gorm", "version": "1.24.2", "license": "MIT", "is_direct": True, "repo": "https://github.com/go-gorm/gorm", "maint_score": 88, "status": "OK"},
        {"name": "gopkg.in/yaml.v3", "version": "3.0.1", "license": "MIT", "is_direct": True, "repo": "https://github.com/go-yaml/yaml", "maint_score": 95, "status": "OK"},
        {"name": "github.com/lib/pq", "version": "1.10.7", "license": "MIT", "is_direct": True, "repo": "https://github.com/lib/pq", "maint_score": 65, "status": "INACTIVE"},

        # Transitives Go dependencies
        {"name": "github.com/gin-contrib/sse", "version": "0.1.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/gin-contrib/sse", "maint_score": 60, "status": "OK"},
        {"name": "github.com/mattn/go-isatty", "version": "0.0.16", "license": "MIT", "is_direct": False, "repo": "https://github.com/mattn/go-isatty", "maint_score": 85, "status": "OK"},
        {"name": "github.com/ugorji/go/codec", "version": "1.2.7", "license": "MIT", "is_direct": False, "repo": "https://github.com/ugorji/go", "maint_score": 35, "status": "OK"},
        {"name": "go.uber.org/multierr", "version": "1.9.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/uber-go/multierr", "maint_score": 80, "status": "OK"},
        {"name": "go.uber.org/atomic", "version": "1.10.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/uber-go/atomic", "maint_score": 82, "status": "OK"},
        {"name": "github.com/jinzhu/inflection", "version": "1.0.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/jinzhu/inflection", "maint_score": 50, "status": "OK"},
        {"name": "github.com/jinzhu/now", "version": "1.1.5", "license": "MIT", "is_direct": False, "repo": "https://github.com/jinzhu/now", "maint_score": 55, "status": "OK"},
        {"name": "golang.org/x/crypto", "version": "0.8.0", "license": "BSD-3-Clause", "is_direct": False, "repo": "https://github.com/golang/crypto", "maint_score": 90, "status": "OK"},
        {"name": "golang.org/x/net", "version": "0.9.0", "license": "BSD-3-Clause", "is_direct": False, "repo": "https://github.com/golang/net", "maint_score": 88, "status": "OK"}
    ]
    go_edges = [
        {"from": "github.com/gin-gonic/gin", "to": "github.com/gin-contrib/sse"},
        {"from": "github.com/gin-gonic/gin", "to": "github.com/mattn/go-isatty"},
        {"from": "github.com/gin-gonic/gin", "to": "github.com/ugorji/go/codec"},
        {"from": "github.com/gin-gonic/gin", "to": "golang.org/x/net"},
        {"from": "go.uber.org/zap", "to": "go.uber.org/multierr"},
        {"from": "go.uber.org/zap", "to": "go.uber.org/atomic"},
        {"from": "gorm.io/gorm", "to": "github.com/jinzhu/inflection"},
        {"from": "gorm.io/gorm", "to": "github.com/jinzhu/now"},
        {"from": "github.com/go-playground/validator/v10", "to": "golang.org/x/crypto"}
    ]

    # .NET Tree Definition (20-40 nodes)
    dotnet_deps = [
        {"name": "Newtonsoft.Json", "version": "13.0.1", "license": "MIT", "is_direct": True, "repo": "https://github.com/JamesNK/Newtonsoft.Json", "maint_score": 98, "status": "OK"},
        {"name": "Microsoft.EntityFrameworkCore", "version": "7.0.5", "license": "MIT", "is_direct": True, "repo": "https://github.com/dotnet/efcore", "maint_score": 95, "status": "OK"},
        {"name": "Microsoft.AspNetCore.Authentication.JwtBearer", "version": "7.0.5", "license": "MIT", "is_direct": True, "repo": "https://github.com/dotnet/aspnetcore", "maint_score": 95, "status": "OK"},
        {"name": "Serilog", "version": "2.12.0", "license": "Apache-2.0", "is_direct": True, "repo": "https://github.com/serilog/serilog", "maint_score": 88, "status": "OK"},
        {"name": "Swashbuckle.AspNetCore", "version": "6.5.0", "license": "MIT", "is_direct": True, "repo": "https://github.com/domaindrivendev/Swashbuckle.AspNetCore", "maint_score": 60, "status": "INACTIVE"},
        {"name": "MediatR", "version": "12.0.1", "license": "Apache-2.0", "is_direct": True, "repo": "https://github.com/jbogard/MediatR", "maint_score": 85, "status": "OK"},
        {"name": "Polly", "version": "7.2.3", "license": "BSD-3-Clause", "is_direct": True, "repo": "https://github.com/App-vNext/Polly", "maint_score": 90, "status": "OK"},

        # Transitives .NET dependencies
        {"name": "Microsoft.IdentityModel.Tokens", "version": "6.30.1", "license": "MIT", "is_direct": False, "repo": "https://github.com/AzureAD/azure-activedirectory-identitymodel-extensions-for-dotnet", "maint_score": 90, "status": "OK"},
        {"name": "System.IdentityModel.Tokens.Jwt", "version": "6.30.1", "license": "MIT", "is_direct": False, "repo": "https://github.com/AzureAD/azure-activedirectory-identitymodel-extensions-for-dotnet", "maint_score": 90, "status": "OK"},
        {"name": "Microsoft.EntityFrameworkCore.Abstractions", "version": "7.0.5", "license": "MIT", "is_direct": False, "repo": "https://github.com/dotnet/efcore", "maint_score": 95, "status": "OK"},
        {"name": "Microsoft.EntityFrameworkCore.Relational", "version": "7.0.5", "license": "MIT", "is_direct": False, "repo": "https://github.com/dotnet/efcore", "maint_score": 95, "status": "OK"},
        {"name": "Swashbuckle.AspNetCore.Swagger", "version": "6.5.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/domaindrivendev/Swashbuckle.AspNetCore", "maint_score": 60, "status": "INACTIVE"},
        {"name": "Swashbuckle.AspNetCore.SwaggerGen", "version": "6.5.0", "license": "MIT", "is_direct": False, "repo": "https://github.com/domaindrivendev/Swashbuckle.AspNetCore", "maint_score": 60, "status": "INACTIVE"}
    ]
    dotnet_edges = [
        {"from": "Microsoft.AspNetCore.Authentication.JwtBearer", "to": "Microsoft.IdentityModel.Tokens"},
        {"from": "Microsoft.AspNetCore.Authentication.JwtBearer", "to": "System.IdentityModel.Tokens.Jwt"},
        {"from": "Microsoft.EntityFrameworkCore", "to": "Microsoft.EntityFrameworkCore.Abstractions"},
        {"from": "Microsoft.EntityFrameworkCore", "to": "Microsoft.EntityFrameworkCore.Relational"},
        {"from": "Swashbuckle.AspNetCore", "to": "Swashbuckle.AspNetCore.Swagger"},
        {"from": "Swashbuckle.AspNetCore", "to": "Swashbuckle.AspNetCore.SwaggerGen"}
    ]

    applications_data = [
        {
            "name": "Core Payment Gateway", 
            "description": "High-throughput transaction dispatch engine interfacing with Swift and clearing houses.", 
            "tech": "Java",
            "score": 85,
            "category": "CRITICAL",
            "vuln_sub": 95,
            "license_sub": 90,
            "maint_sub": 65,
            "summary": "The application has several critical production vulnerabilities including Log4Shell and Spring4Shell alongside outdated dependencies and GPL license compliance violations requiring immediate remediation.",
            "actions": [
                {"title": "Upgrade log4j-core to 2.17.1+", "description": "Immediate critical security patch needed to address CVE-2021-44228 (Log4Shell) in central logging framework.", "priority": "HIGH"},
                {"title": "Upgrade spring-core to 5.3.18+", "description": "Remediate CVE-2022-22965 (Spring4Shell) RCE exposure in application container layer.", "priority": "HIGH"},
                {"title": "Remediate GPL-3.0 License compliance", "description": "Replace GORM/GPL strong copyleft dependency with MIT/Apache components to clear internal distribution conflicts.", "priority": "HIGH"}
            ]
        },
        {
            "name": "Retail Banking API", 
            "description": "Backend services supplying client checkings, savings, and transfers dashboards.", 
            "tech": "Node.js",
            "score": 54,
            "category": "MEDIUM",
            "vuln_sub": 55,
            "license_sub": 10,
            "maint_sub": 50,
            "summary": "The application contains moderate dependency maintenance issues and several medium severity vulnerabilities in its Node.js Express framework.",
            "actions": [
                {"title": "Upgrade axios to 1.6.0+", "description": "Resolves medium and high vulnerability signatures regarding request request routing bypass.", "priority": "HIGH"},
                {"title": "Update express to 4.18.1", "description": "Remediation updates to secure parsing vulnerabilities in body-parser transitives.", "priority": "MEDIUM"},
                {"title": "Replace unmaintained compression library", "description": "Decommission deprecated compression package in favor of modern streaming solutions.", "priority": "LOW"}
            ]
        },
        {
            "name": "Customer Identity Service", 
            "description": "Corporate SSO and customer identity provider utilizing OAuth2 and OpenID Connect.", 
            "tech": "Python",
            "score": 91,
            "category": "CRITICAL",
            "vuln_sub": 96,
            "license_sub": 90,
            "maint_sub": 85,
            "summary": "Critical security posture identified: Multiple critical and high CVSS vulnerabilities found in identity resolution modules alongside abandoned, unmaintained dependencies and weak licensing markers.",
            "actions": [
                {"title": "Upgrade cryptography tool to 39.0.1+", "description": "Mitigate critical vulnerability CVE-2023-23931 affecting key signing parameters.", "priority": "HIGH"},
                {"title": "Replace unmaintained websockets tool", "description": "Deprecated and inactive websockets packages present threat surface for denial-of-service vectors.", "priority": "HIGH"},
                {"title": "Resolve AGPL-3.0 license conflict", "description": "Audit starlette library usage rules or replace with modern BSD-licensed wrapper interfaces.", "priority": "HIGH"}
            ]
        },
        {
            "name": "Mobile Banking Backend", 
            "description": "Orchestration API layer supporting secure native iOS and Android application clients.", 
            "tech": "Node.js",
            "score": 78,
            "category": "HIGH",
            "vuln_sub": 80,
            "license_sub": 30,
            "maint_sub": 60,
            "summary": "The mobile backend system contains high severity vulnerability triggers within axios and jsonwebtoken alongside unmaintained libraries.",
            "actions": [
                {"title": "Upgrade jsonwebtoken dependency", "description": "Fix key validation vulnerabilities to prevent JWT signature forge capabilities.", "priority": "HIGH"},
                {"title": "Patch axios request routing", "description": "Upgrade to latest secure axios builds to resolve server-side request forgery risks.", "priority": "HIGH"}
            ]
        },
        {
            "name": "Fraud Detection Engine", 
            "description": "Real-time transaction profiling using transaction histories and custom security rules.", 
            "tech": "Python",
            "score": 72,
            "category": "HIGH",
            "vuln_sub": 75,
            "license_sub": 60,
            "maint_sub": 70,
            "summary": "The application contains severe TensorFlow vulnerability concerns alongside outdated Requests libraries and several deprecated Python packages.",
            "actions": [
                {"title": "Upgrade tensorflow module to 2.6.2+", "description": "Remediate severe memory corruption vulnerabilities and tensor compiler RCE exploits.", "priority": "HIGH"},
                {"title": "Upgrade requests to 2.27.0+", "description": "Mitigate HTTP header injection vulnerability CVE-2021-43818.", "priority": "HIGH"},
                {"title": "Replace deprecated packages", "description": "Migrate inactive and deprecated yaml helper utilities to fully-maintained alternatives.", "priority": "MEDIUM"}
            ]
        },
        {
            "name": "Transaction Processing Service", 
            "description": "Distributed ledger processing ledger entries for all retail asset balances.", 
            "tech": "Go",
            "score": 48,
            "category": "MEDIUM",
            "vuln_sub": 45,
            "license_sub": 30,
            "maint_sub": 40,
            "summary": "The service exhibits moderate vulnerability and maintenance issues in package cryptography routines.",
            "actions": [
                {"title": "Upgrade golang.org/x/crypto", "description": "Patch low-risk side channel attack parameters within cryptographic signing keys.", "priority": "MEDIUM"},
                {"title": "Schedule regular audit checks", "description": "Incorporate automated vulnerability assessments into compile pipelines.", "priority": "LOW"}
            ]
        },
        {
            "name": "Investment Portfolio API", 
            "description": "Calculates holdings valuations, yields, and tracks corporate actions.", 
            "tech": "Java",
            "score": 18,
            "category": "LOW",
            "vuln_sub": 10,
            "license_sub": 10,
            "maint_sub": 20,
            "summary": "The application demonstrates a healthy software supply chain with only minor maintenance observations.",
            "actions": [
                {"title": "Verify dependency status checks", "description": "Continue monitoring package versions regularly via automated CI policies.", "priority": "LOW"}
            ]
        },
        {
            "name": "Loan Management Platform", 
            "description": "Calculates amortization schedules and coordinates credit rating queries.", 
            "tech": "Java",
            "score": 68,
            "category": "HIGH",
            "vuln_sub": 70,
            "license_sub": 30,
            "maint_sub": 60,
            "summary": "High risk rating caused by outdated logging packages and Hibernate ORM serialization concerns.",
            "actions": [
                {"title": "Upgrade logback-classic logger", "description": "Remediate JNDI lookup vulnerabilities causing remote code executions.", "priority": "HIGH"},
                {"title": "Upgrade hibernate-core utility", "description": "Mitigate database query injection vulnerabilities.", "priority": "HIGH"}
            ]
        },
        {
            "name": "Notification Service", 
            "description": "Centralized alerts manager handling email, push notifications, and SMS triggers.", 
            "tech": "Go",
            "score": 42,
            "category": "MEDIUM",
            "vuln_sub": 30,
            "license_sub": 60,
            "maint_sub": 35,
            "summary": "The application has moderate dependency health, but exhibits licensing compliance exposure with strong copyleft components (GPL) integrated into proprietary code boundaries.",
            "actions": [
                {"title": "Remediate GORM GPL license", "description": "GORM package references strong copyleft GPL licensing metrics, requiring compliance isolation.", "priority": "HIGH"},
                {"title": "Upgrade validator to 10.11.0+", "description": "Resolve medium severity buffer overflow triggers.", "priority": "MEDIUM"}
            ]
        },
        {
            "name": "Authentication Service", 
            "description": "Provides JWT credentials signing and manages corporate active directories.", 
            "tech": ".NET",
            "score": 15,
            "category": "LOW",
            "vuln_sub": 10,
            "license_sub": 10,
            "maint_sub": 15,
            "summary": "The application demonstrates a healthy software supply chain with only minor maintenance observations and no active CVE threats.",
            "actions": [
                {"title": "Upgrade Newtonsoft.Json configuration", "description": "Routine security patching update to version 13.0.3.", "priority": "LOW"}
            ]
        },
        {
            "name": "Treasury Operations API", 
            "description": "Internal liquidity management, cash positioning, and forex reconciliation services.", 
            "tech": "Java",
            "score": 38,
            "category": "MEDIUM",
            "vuln_sub": 35,
            "license_sub": 20,
            "maint_sub": 45,
            "summary": "The application has minor vulnerabilities in tomcat embedded dependencies.",
            "actions": [
                {"title": "Upgrade tomcat embedded packages", "description": "Mitigate medium severity denial-of-service vulnerabilities.", "priority": "MEDIUM"}
            ]
        },
        {
            "name": "Card Authorization Engine", 
            "description": "Orchestrates instant authorization approvals with Mastercard and Visa networks.", 
            "tech": ".NET",
            "score": 10,
            "category": "LOW",
            "vuln_sub": 5,
            "license_sub": 5,
            "maint_sub": 10,
            "summary": "The card authorization engine exhibits excellent supply chain status with no active vulnerabilities.",
            "actions": [
                {"title": "Continue weekly automated scans", "description": "Track upstream nuget changes inside core transaction packages.", "priority": "LOW"}
            ]
        }
    ]

    # Create applications and build analysis records
    for app_info in applications_data:
        print(f"Creating application: {app_info['name']}")
        app = Application(
            id=uuid.uuid4(),
            name=app_info["name"],
            description=app_info["description"]
        )
        session.add(app)
        session.flush()

        # Get stack data
        tech = app_info["tech"]
        if tech == "Java":
            deps_src, edges_src = java_deps, java_edges
            sbom_format = "CycloneDX"
        elif tech == "Node.js":
            deps_src, edges_src = nodejs_deps, nodejs_edges
            sbom_format = "CycloneDX"
        elif tech == "Python":
            deps_src, edges_src = python_deps, python_edges
            sbom_format = "CycloneDX"
        elif tech == "Go":
            deps_src, edges_src = go_deps, go_edges
            sbom_format = "CycloneDX"
        else:
            deps_src, edges_src = dotnet_deps, dotnet_edges
            sbom_format = "CycloneDX"

        # Generate CycloneDX JSON structure and write to stored file
        components = []
        bom_ref_map = {}
        for d in deps_src:
            bom_ref = f"pkg:{tech.lower()}/{d['name']}@{d['version']}"
            bom_ref_map[d['name']] = bom_ref
            components.append({
                "name": d["name"],
                "version": d["version"],
                "type": "library",
                "purl": bom_ref,
                "licenses": [{"license": {"id": d["license"]}}],
                "externalReferences": [{"type": "vcs", "url": d["repo"]}]
            })

        ref_map = {}
        # Connect root component to all direct dependencies
        root_children = [bom_ref_map[d["name"]] for d in deps_src if d["is_direct"]]
        ref_map["root-app"] = root_children

        # Connect other transitives
        for edge in edges_src:
            from_ref = bom_ref_map.get(edge["from"])
            to_ref = bom_ref_map.get(edge["to"])
            if from_ref and to_ref:
                ref_map.setdefault(from_ref, []).append(to_ref)

        dependencies_section = []
        for ref, deps in ref_map.items():
            dependencies_section.append({
                "ref": ref,
                "dependsOn": deps
            })

        sbom_data = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": "2026-07-11T12:00:00Z",
                "component": {
                    "bom-ref": "root-app",
                    "name": app_info["name"].lower().replace(" ", "-"),
                    "version": "1.0.0",
                    "type": "application"
                }
            },
            "components": components,
            "dependencies": dependencies_section
        }

        filename_stored = f"{uuid.uuid4()}.json"
        original_filename = f"{app_info['name'].lower().replace(' ', '_')}_cyclonedx.json"
        sbom_file_path = os.path.join(settings.SBOM_STORAGE_PATH, filename_stored)
        
        with open(sbom_file_path, "w") as f:
            json.dump(sbom_data, f)

        # Create Sbom record
        sbom = Sbom(
            id=uuid.uuid4(),
            application_id=app.id,
            original_filename=original_filename,
            filename_stored=filename_stored,
            format="CycloneDX",
            status="completed",
            component_count=len(components)
        )
        session.add(sbom)
        session.flush()

        # Insert Dependencies & Edges
        dep_id_map = {}
        for d in deps_src:
            dep = Dependency(
                id=uuid.uuid4(),
                sbom_id=sbom.id,
                name=d["name"],
                version=d["version"],
                ecosystem=tech.lower(),
                purl=bom_ref_map.get(d["name"]),
                license_id=d["license"],
                is_direct=d["is_direct"],
                repo_url=d["repo"]
            )
            session.add(dep)
            session.flush()
            dep_id_map[d["name"]] = dep.id

            # Insert Maintenance Signals
            ms = MaintenanceSignal(
                id=uuid.uuid4(),
                dependency_id=dep.id,
                stars=500 + d["maint_score"] * 100,
                is_archived=(d["status"] == "ARCHIVED"),
                release_frequency_days=30 if d["status"] == "OK" else 180 if d["status"] == "INACTIVE" else None,
                maintenance_score=d["maint_score"],
                status="OK"
            )
            session.add(ms)

        # Insert Dependency Edges
        for edge in edges_src:
            from_id = dep_id_map.get(edge["from"])
            to_id = dep_id_map.get(edge["to"])
            if from_id and to_id:
                de = DependencyEdge(
                    id=uuid.uuid4(),
                    sbom_id=sbom.id,
                    from_dependency_id=from_id,
                    to_dependency_id=to_id
                )
                session.add(de)

        # Add mock vulnerabilities based on application risk level
        vuln_count = 0
        if app_info["category"] == "CRITICAL":
            vuln_count = 22
        elif app_info["category"] == "HIGH":
            vuln_count = 14
        elif app_info["category"] == "MEDIUM":
            vuln_count = 7
        elif app_info["category"] == "LOW":
            vuln_count = 2

        # Distribute vulnerabilities among dependencies
        cve_counter = 1001
        for v_idx in range(vuln_count):
            # Pick a dependency to attach vulnerability
            dep_name = deps_src[v_idx % len(deps_src)]["name"]
            dep_id = dep_id_map[dep_name]
            
            severity = "CRITICAL" if v_idx < vuln_count * 0.2 else "HIGH" if v_idx < vuln_count * 0.5 else "MEDIUM" if v_idx < vuln_count * 0.8 else "LOW"
            cve_id = f"CVE-2023-{cve_counter}"
            cve_counter += 1

            vuln = Vulnerability(
                id=uuid.uuid4(),
                dependency_id=dep_id,
                vuln_id=cve_id,
                severity=severity,
                summary=f"Vulnerability affecting component {dep_name} due to invalid input validation rules.",
                fixed_version="2.0.0",
                source="osv"
            )
            session.add(vuln)

        # Compile Breakdown Json for Risk Report
        top_contribs = []
        for d in deps_src[:5]:
            license_risk = "HIGH" if d["license"] in ["GPL-3.0-only", "AGPL-3.0-or-later", "GPL-3.0-or-later", "GPL-2.0"] else "MEDIUM" if d["license"] == "LGPL-2.1-or-later" else "NONE"
            top_contribs.append({
                "name": d["name"],
                "version": d["version"],
                "is_direct": d["is_direct"],
                "vuln_score": 90 if app_info["category"] == "CRITICAL" else 50 if app_info["category"] == "MEDIUM" else 10,
                "license_score": 90 if license_risk == "HIGH" else 30 if license_risk == "MEDIUM" else 0,
                "weighted_contribution": 15 if app_info["category"] == "CRITICAL" else 5
            })

        breakdown_json = {
            "top_contributing_dependencies": top_contribs
        }

        # Create Risk Report
        report = RiskReport(
            id=uuid.uuid4(),
            sbom_id=sbom.id,
            application_id=app.id,
            overall_score=app_info["score"],
            category=app_info["category"],
            vulnerability_subscore=app_info["vuln_sub"],
            license_subscore=app_info["license_sub"],
            maintenance_subscore=app_info["maint_sub"],
            breakdown_json=breakdown_json,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        session.add(report)
        session.flush()

        # Create AI Report
        ai_report = AIReport(
            id=uuid.uuid4(),
            risk_report_id=report.id,
            summary=app_info["summary"],
            top_actions_json=app_info["actions"],
            model_used="gemini-3.5-flash",
            fallback_used=False,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        session.add(ai_report)

        # Update latest score on Application
        app.latest_score = app_info["score"]
        app.latest_category = app_info["category"]
        app.last_analyzed_at = datetime.datetime.now(datetime.timezone.utc)
        session.add(app)
        session.commit()
        print(f"Successfully populated and scored {app_info['name']}.")

    session.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed()
