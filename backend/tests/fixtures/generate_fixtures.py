import os
import json
import uuid

# Defined tech stack configurations with 20-35 components
java_components = [
    {"name": "org.springframework:spring-core", "version": "5.3.15", "license": "Apache-2.0", "repo": "https://github.com/spring-projects/spring-framework", "is_direct": True},
    {"name": "org.apache.logging.log4j:log4j-core", "version": "2.14.1", "license": "Apache-2.0", "repo": "https://github.com/apache/logging-log4j2", "is_direct": True},
    {"name": "org.hibernate:hibernate-core", "version": "5.6.0.Final", "license": "LGPL-2.1-or-later", "repo": "https://github.com/hibernate/hibernate-orm", "is_direct": True},
    {"name": "com.fasterxml.jackson.core:jackson-databind", "version": "2.13.0", "license": "Apache-2.0", "repo": "https://github.com/FasterXML/jackson-databind", "is_direct": True},
    {"name": "org.springframework:spring-web", "version": "5.3.15", "license": "Apache-2.0", "repo": "https://github.com/spring-projects/spring-framework", "is_direct": True},
    {"name": "org.springframework:spring-security", "version": "5.6.0", "license": "Apache-2.0", "repo": "https://github.com/spring-projects/spring-security", "is_direct": True},
    {"name": "org.springframework:spring-data-jpa", "version": "2.6.0", "license": "Apache-2.0", "repo": "https://github.com/spring-projects/spring-data-jpa", "is_direct": True},
    {"name": "commons-io:commons-io", "version": "2.11.0", "license": "Apache-2.0", "repo": "https://github.com/apache/commons-io", "is_direct": True},
    {"name": "tomcat-embed-core", "version": "9.0.58", "license": "Apache-2.0", "repo": "https://github.com/apache/tomcat", "is_direct": True},
    {"name": "com.zaxxer:HikariCP", "version": "4.0.3", "license": "Apache-2.0", "repo": "https://github.com/brettwooldridge/HikariCP", "is_direct": True},
    # transitive Java dependencies
    {"name": "org.springframework:spring-jcl", "version": "5.3.15", "license": "Apache-2.0", "repo": "https://github.com/spring-projects/spring-framework", "is_direct": False},
    {"name": "org.springframework:spring-beans", "version": "5.3.15", "license": "Apache-2.0", "repo": "https://github.com/spring-projects/spring-framework", "is_direct": False},
    {"name": "org.springframework:spring-aop", "version": "5.3.15", "license": "Apache-2.0", "repo": "https://github.com/spring-projects/spring-framework", "is_direct": False},
    {"name": "org.springframework:spring-expression", "version": "5.3.15", "license": "Apache-2.0", "repo": "https://github.com/spring-projects/spring-framework", "is_direct": False},
    {"name": "org.springframework:spring-security-core", "version": "5.6.0", "license": "Apache-2.0", "repo": "https://github.com/spring-projects/spring-security", "is_direct": False},
    {"name": "org.springframework:spring-security-web", "version": "5.6.0", "license": "Apache-2.0", "repo": "https://github.com/spring-projects/spring-security", "is_direct": False},
    {"name": "com.fasterxml.jackson.core:jackson-annotations", "version": "2.13.0", "license": "Apache-2.0", "repo": "https://github.com/FasterXML/jackson-annotations", "is_direct": False},
    {"name": "com.fasterxml.jackson.core:jackson-core", "version": "2.13.0", "license": "Apache-2.0", "repo": "https://github.com/FasterXML/jackson-core", "is_direct": False},
    {"name": "org.jboss.logging:jboss-logging", "version": "3.4.2.Final", "license": "Apache-2.0", "repo": "https://github.com/jboss-logging/jboss-logging", "is_direct": False},
    {"name": "com.fasterxml:classmate", "version": "1.5.1", "license": "Apache-2.0", "repo": "https://github.com/FasterXML/java-classmate", "is_direct": False},
    {"name": "antlr:antlr", "version": "2.7.7", "license": "BSD-3-Clause", "repo": "https://github.com/antlr/antlr4", "is_direct": False},
    {"name": "dom4j:dom4j", "version": "2.1.3", "license": "BSD-3-Clause", "repo": "https://github.com/dom4j/dom4j", "is_direct": False},
    {"name": "ch.qos.logback:logback-classic", "version": "1.2.10", "license": "EPL-1.0", "repo": "https://github.com/qos-ch/logback", "is_direct": False},
    {"name": "ch.qos.logback:logback-core", "version": "1.2.10", "license": "EPL-1.0", "repo": "https://github.com/qos-ch/logback", "is_direct": False},
    {"name": "org.slf4j:slf4j-api", "version": "1.7.32", "license": "MIT", "repo": "https://github.com/qos-ch/slf4j", "is_direct": False},
    {"name": "org.apache.logging.log4j:log4j-api", "version": "2.14.1", "license": "Apache-2.0", "repo": "https://github.com/apache/logging-log4j2", "is_direct": False},
    {"name": "tomcat-annotations-api", "version": "9.0.58", "license": "Apache-2.0", "repo": "https://github.com/apache/tomcat", "is_direct": False},
    {"name": "org.apache.commons:commons-lang3", "version": "3.12.0", "license": "Apache-2.0", "repo": "https://github.com/apache/commons-lang", "is_direct": False},
    {"name": "io.micrometer:micrometer-core", "version": "1.8.2", "license": "Apache-2.0", "repo": "https://github.com/micrometer-metrics/micrometer", "is_direct": False},
    {"name": "org.hdrhistogram:HdrHistogram", "version": "2.1.12", "license": "BSD-2-Clause", "repo": "https://github.com/HdrHistogram/HdrHistogram", "is_direct": False}
]
java_edges = [
    ("org.springframework:spring-core", "org.springframework:spring-jcl"),
    ("org.springframework:spring-core", "ch.qos.logback:logback-classic"),
    ("org.springframework:spring-core", "org.apache.commons:commons-lang3"),
    ("org.springframework:spring-core", "io.micrometer:micrometer-core"),
    ("org.springframework:spring-web", "org.springframework:spring-beans"),
    ("org.springframework:spring-web", "org.springframework:spring-aop"),
    ("org.springframework:spring-security", "org.springframework:spring-security-core"),
    ("org.springframework:spring-security", "org.springframework:spring-security-web"),
    ("org.springframework:spring-security-web", "org.springframework:spring-expression"),
    ("org.springframework:spring-data-jpa", "org.springframework:spring-beans"),
    ("com.fasterxml.jackson.core:jackson-databind", "com.fasterxml.jackson.core:jackson-annotations"),
    ("com.fasterxml.jackson.core:jackson-databind", "com.fasterxml.jackson.core:jackson-core"),
    ("org.hibernate:hibernate-core", "org.jboss.logging:jboss-logging"),
    ("org.hibernate:hibernate-core", "com.fasterxml:classmate"),
    ("org.hibernate:hibernate-core", "antlr:antlr"),
    ("org.hibernate:hibernate-core", "dom4j:dom4j"),
    ("ch.qos.logback:logback-classic", "ch.qos.logback:logback-core"),
    ("ch.qos.logback:logback-classic", "org.slf4j:slf4j-api"),
    ("org.apache.logging.log4j:log4j-core", "org.apache.logging.log4j:log4j-api"),
    ("tomcat-embed-core", "tomcat-annotations-api"),
    ("io.micrometer:micrometer-core", "org.hdrhistogram:HdrHistogram")
]

nodejs_components = [
    {"name": "express", "version": "4.17.1", "license": "MIT", "repo": "https://github.com/expressjs/express", "is_direct": True},
    {"name": "helmet", "version": "5.0.2", "license": "MIT", "repo": "https://github.com/helmetjs/helmet", "is_direct": True},
    {"name": "cors", "version": "2.8.5", "license": "MIT", "repo": "https://github.com/expressjs/cors", "is_direct": True},
    {"name": "axios", "version": "0.21.1", "license": "MIT", "repo": "https://github.com/axios/axios", "is_direct": True},
    {"name": "jsonwebtoken", "version": "8.5.1", "license": "MIT", "repo": "https://github.com/auth0/node-jsonwebtoken", "is_direct": True},
    {"name": "bcrypt", "version": "5.0.1", "license": "BSD-3-Clause", "repo": "https://github.com/kelektiv/node.bcrypt.js", "is_direct": True},
    {"name": "dotenv", "version": "16.0.0", "license": "BSD-2-Clause", "repo": "https://github.com/motdotla/dotenv", "is_direct": True},
    {"name": "winston", "version": "3.6.0", "license": "MIT", "repo": "https://github.com/winstonjs/winston", "is_direct": True},
    {"name": "mongoose", "version": "6.2.2", "license": "MIT", "repo": "https://github.com/Automattic/mongoose", "is_direct": True},
    {"name": "compression", "version": "1.7.4", "license": "MIT", "repo": "https://github.com/expressjs/compression", "is_direct": True},
    # transitive Node.js dependencies
    {"name": "body-parser", "version": "1.19.0", "license": "MIT", "repo": "https://github.com/expressjs/body-parser", "is_direct": False},
    {"name": "debug", "version": "4.3.1", "license": "MIT", "repo": "https://github.com/debug-js/debug", "is_direct": False},
    {"name": "ms", "version": "2.1.2", "license": "MIT", "repo": "https://github.com/vercel/ms", "is_direct": False},
    {"name": "accepts", "version": "1.3.7", "license": "MIT", "repo": "https://github.com/jshttp/accepts", "is_direct": False},
    {"name": "mime-types", "version": "2.1.27", "license": "MIT", "repo": "https://github.com/jshttp/mime-types", "is_direct": False},
    {"name": "negotiator", "version": "0.6.2", "license": "MIT", "repo": "https://github.com/jshttp/negotiator", "is_direct": False},
    {"name": "send", "version": "0.17.1", "license": "MIT", "repo": "https://github.com/pillarjs/send", "is_direct": False},
    {"name": "mime", "version": "1.6.0", "license": "MIT", "repo": "https://github.com/broofa/mime", "is_direct": False},
    {"name": "etag", "version": "1.8.1", "license": "MIT", "repo": "https://github.com/jshttp/etag", "is_direct": False},
    {"name": "follow-redirects", "version": "1.14.1", "license": "MIT", "repo": "https://github.com/follow-redirects/follow-redirects", "is_direct": False},
    {"name": "form-data", "version": "4.0.0", "license": "MIT", "repo": "https://github.com/form-data/form-data", "is_direct": False},
    {"name": "asynckit", "version": "0.4.0", "license": "MIT", "repo": "https://github.com/caolan/asynckit", "is_direct": False},
    {"name": "combined-stream", "version": "1.0.8", "license": "MIT", "repo": "https://github.com/felixge/node-combined-stream", "is_direct": False},
    {"name": "mime-db", "version": "1.44.0", "license": "MIT", "repo": "https://github.com/jshttp/mime-db", "is_direct": False},
    {"name": "mongodb", "version": "4.3.1", "license": "Apache-2.0", "repo": "https://github.com/mongodb/node-mongodb-native", "is_direct": False},
    {"name": "mpath", "version": "0.8.4", "license": "MIT", "repo": "https://github.com/aheckmann/mpath", "is_direct": False},
    {"name": "mquery", "version": "4.0.2", "license": "MIT", "repo": "https://github.com/aheckmann/mquery", "is_direct": False},
    {"name": "kareem", "version": "2.3.4", "license": "MIT", "repo": "https://github.com/aheckmann/kareem", "is_direct": False},
    {"name": "safe-buffer", "version": "5.2.1", "license": "MIT", "repo": "https://github.com/feross/safe-buffer", "is_direct": False},
    {"name": "cookie", "version": "0.4.1", "license": "MIT", "repo": "https://github.com/jshttp/cookie", "is_direct": False},
    {"name": "qs", "version": "6.7.0", "license": "BSD-3-Clause", "repo": "https://github.com/ljharb/qs", "is_direct": False},
    {"name": "vary", "version": "1.1.2", "license": "MIT", "repo": "https://github.com/jshttp/vary", "is_direct": False}
]
nodejs_edges = [
    ("express", "body-parser"),
    ("express", "debug"),
    ("express", "accepts"),
    ("express", "send"),
    ("express", "qs"),
    ("accepts", "mime-types"),
    ("accepts", "negotiator"),
    ("mime-types", "mime-db"),
    ("send", "mime"),
    ("send", "etag"),
    ("debug", "ms"),
    ("axios", "follow-redirects"),
    ("axios", "form-data"),
    ("form-data", "asynckit"),
    ("form-data", "combined-stream"),
    ("jsonwebtoken", "ms"),
    ("mongoose", "mongodb"),
    ("mongoose", "mpath"),
    ("mongoose", "mquery"),
    ("mongoose", "kareem"),
    ("express", "cookie"),
    ("express", "vary")
]

python_components = [
    {"name": "fastapi", "version": "0.85.0", "license": "MIT", "repo": "https://github.com/tiangolo/fastapi", "is_direct": True},
    {"name": "starlette", "version": "0.20.4", "license": "BSD-3-Clause", "repo": "https://github.com/encode/starlette", "is_direct": True},
    {"name": "pydantic", "version": "1.10.2", "license": "MIT", "repo": "https://github.com/pydantic/pydantic", "is_direct": True},
    {"name": "uvicorn", "version": "0.18.3", "license": "BSD-3-Clause", "repo": "https://github.com/encode/uvicorn", "is_direct": True},
    {"name": "sqlalchemy", "version": "1.4.41", "license": "MIT", "repo": "https://github.com/sqlalchemy/sqlalchemy", "is_direct": True},
    {"name": "requests", "version": "2.28.1", "license": "Apache-2.0", "repo": "https://github.com/psf/requests", "is_direct": True},
    {"name": "jinja2", "version": "3.1.2", "license": "BSD-3-Clause", "repo": "https://github.com/pallets/jinja", "is_direct": True},
    {"name": "urllib3", "version": "1.26.12", "license": "MIT", "repo": "https://github.com/urllib3/urllib3", "is_direct": True},
    # transitive Python dependencies
    {"name": "click", "version": "8.1.3", "license": "BSD-3-Clause", "repo": "https://github.com/pallets/click", "is_direct": False},
    {"name": "certifi", "version": "2022.9.24", "license": "MPL-2.0", "repo": "https://github.com/certifi/python-certifi", "is_direct": False},
    {"name": "h11", "version": "0.14.0", "license": "MIT", "repo": "https://github.com/python-hyper/h11", "is_direct": False},
    {"name": "websockets", "version": "10.3", "license": "BSD-3-Clause", "repo": "https://github.com/aaugustin/websockets", "is_direct": False},
    {"name": "greenlet", "version": "1.1.3", "license": "MIT", "repo": "https://github.com/python-greenlet/greenlet", "is_direct": False},
    {"name": "idna", "version": "3.4", "license": "BSD-3-Clause", "repo": "https://github.com/kjd/idna", "is_direct": False},
    {"name": "charset-normalizer", "version": "2.1.1", "license": "MIT", "repo": "https://github.com/Ousret/charset-normalizer", "is_direct": False},
    {"name": "markupsafe", "version": "2.1.1", "license": "BSD-3-Clause", "repo": "https://github.com/pallets/markupsafe", "is_direct": False},
    {"name": "anyio", "version": "3.6.1", "license": "MIT", "repo": "https://github.com/agronholm/anyio", "is_direct": False},
    {"name": "sniffio", "version": "1.3.0", "license": "Apache-2.0", "repo": "https://github.com/python-attrs/sniffio", "is_direct": False},
    {"name": "typing-extensions", "version": "4.3.0", "license": "PSF-2.0", "repo": "https://github.com/python/typing_extensions", "is_direct": False},
    {"name": "email-validator", "version": "1.3.0", "license": "MIT", "repo": "https://github.com/kushal-das/email_validator", "is_direct": False},
    {"name": "dnspython", "version": "2.2.1", "license": "ISC", "repo": "https://github.com/rthalley/dnspython", "is_direct": False}
]
python_edges = [
    ("fastapi", "starlette"),
    ("fastapi", "pydantic"),
    ("fastapi", "anyio"),
    ("starlette", "anyio"),
    ("anyio", "sniffio"),
    ("uvicorn", "h11"),
    ("uvicorn", "websockets"),
    ("uvicorn", "click"),
    ("sqlalchemy", "greenlet"),
    ("requests", "urllib3"),
    ("requests", "idna"),
    ("requests", "charset-normalizer"),
    ("requests", "certifi"),
    ("jinja2", "markupsafe"),
    ("pydantic", "typing-extensions"),
    ("pydantic", "email-validator"),
    ("email-validator", "dnspython")
]

go_components = [
    {"name": "github.com/gin-gonic/gin", "version": "v1.8.1", "license": "MIT", "repo": "https://github.com/gin-gonic/gin", "is_direct": True},
    {"name": "github.com/go-playground/validator/v10", "version": "v10.11.0", "license": "MIT", "repo": "https://github.com/go-playground/validator", "is_direct": True},
    {"name": "github.com/golang-jwt/jwt/v5", "version": "v5.0.0", "license": "MIT", "repo": "https://github.com/golang-jwt/jwt", "is_direct": True},
    {"name": "go.uber.org/zap", "version": "v1.23.0", "license": "MIT", "repo": "https://github.com/uber-go/zap", "is_direct": True},
    {"name": "gorm.io/gorm", "version": "v1.24.1", "license": "MIT", "repo": "https://github.com/go-gorm/gorm", "is_direct": True},
    {"name": "gopkg.in/yaml.v3", "version": "v3.0.1", "license": "MIT", "repo": "https://github.com/go-yaml/yaml", "is_direct": True},
    {"name": "github.com/lib/pq", "version": "v1.10.7", "license": "MIT", "repo": "https://github.com/lib/pq", "is_direct": True},
    # transitive Go dependencies
    {"name": "github.com/gin-contrib/sse", "version": "v0.1.0", "license": "MIT", "repo": "https://github.com/gin-contrib/sse", "is_direct": False},
    {"name": "github.com/mattn/go-isatty", "version": "v0.0.16", "license": "MIT", "repo": "https://github.com/mattn/go-isatty", "is_direct": False},
    {"name": "github.com/ugorji/go/codec", "version": "v1.2.7", "license": "MIT", "repo": "https://github.com/ugorji/go", "is_direct": False},
    {"name": "go.uber.org/multierr", "version": "v1.8.0", "license": "MIT", "repo": "https://github.com/uber-go/multierr", "is_direct": False},
    {"name": "go.uber.org/atomic", "version": "v1.10.0", "license": "MIT", "repo": "https://github.com/uber-go/atomic", "is_direct": False},
    {"name": "github.com/jinzhu/inflection", "version": "v1.0.0", "license": "MIT", "repo": "https://github.com/jinzhu/inflection", "is_direct": False},
    {"name": "github.com/jinzhu/now", "version": "v1.1.5", "license": "MIT", "repo": "https://github.com/jinzhu/now", "is_direct": False},
    {"name": "golang.org/x/crypto", "version": "v0.1.0", "license": "BSD-3-Clause", "repo": "https://github.com/golang/crypto", "is_direct": False},
    {"name": "golang.org/x/net", "version": "v0.1.0", "license": "BSD-3-Clause", "repo": "https://github.com/golang/net", "is_direct": False},
    {"name": "golang.org/x/sys", "version": "v0.1.0", "license": "BSD-3-Clause", "repo": "https://github.com/golang/sys", "is_direct": False},
    {"name": "golang.org/x/text", "version": "v0.4.0", "license": "BSD-3-Clause", "repo": "https://github.com/golang/text", "is_direct": False},
    {"name": "github.com/leodido/go-urn", "version": "v1.2.1", "license": "BSD-3-Clause", "repo": "https://github.com/leodido/go-urn", "is_direct": False},
    {"name": "github.com/pelletier/go-toml/v2", "version": "v2.0.5", "license": "MIT", "repo": "https://github.com/pelletier/go-toml", "is_direct": False},
    {"name": "github.com/go-playground/universal-translator", "version": "v0.18.0", "license": "MIT", "repo": "https://github.com/go-playground/universal-translator", "is_direct": False},
    {"name": "github.com/go-playground/locales", "version": "v0.14.0", "license": "MIT", "repo": "https://github.com/go-playground/locales", "is_direct": False}
]
go_edges = [
    ("github.com/gin-gonic/gin", "github.com/gin-contrib/sse"),
    ("github.com/gin-gonic/gin", "github.com/mattn/go-isatty"),
    ("github.com/gin-gonic/gin", "github.com/ugorji/go/codec"),
    ("github.com/gin-gonic/gin", "golang.org/x/net"),
    ("github.com/gin-gonic/gin", "github.com/pelletier/go-toml/v2"),
    ("go.uber.org/zap", "go.uber.org/multierr"),
    ("go.uber.org/zap", "go.uber.org/atomic"),
    ("gorm.io/gorm", "github.com/jinzhu/inflection"),
    ("gorm.io/gorm", "github.com/jinzhu/now"),
    ("github.com/go-playground/validator/v10", "golang.org/x/crypto"),
    ("github.com/go-playground/validator/v10", "github.com/leodido/go-urn"),
    ("github.com/go-playground/validator/v10", "github.com/go-playground/universal-translator"),
    ("github.com/go-playground/universal-translator", "github.com/go-playground/locales"),
    ("golang.org/x/net", "golang.org/x/sys"),
    ("golang.org/x/net", "golang.org/x/text")
]

dotnet_components = [
    {"name": "Newtonsoft.Json", "version": "13.0.1", "license": "MIT", "repo": "https://github.com/JamesNK/Newtonsoft.Json", "is_direct": True},
    {"name": "Microsoft.EntityFrameworkCore", "version": "6.0.5", "license": "MIT", "repo": "https://github.com/dotnet/efcore", "is_direct": True},
    {"name": "Microsoft.AspNetCore.Authentication.JwtBearer", "version": "6.0.5", "license": "MIT", "repo": "https://github.com/dotnet/aspnetcore", "is_direct": True},
    {"name": "Serilog", "version": "2.10.0", "license": "Apache-2.0", "repo": "https://github.com/serilog/serilog", "is_direct": True},
    {"name": "Swashbuckle.AspNetCore", "version": "6.3.0", "license": "MIT", "repo": "https://github.com/domaindrivendev/Swashbuckle.AspNetCore", "is_direct": True},
    {"name": "MediatR", "version": "10.0.1", "license": "Apache-2.0", "repo": "https://github.com/jbogard/MediatR", "is_direct": True},
    {"name": "Polly", "version": "7.2.3", "license": "BSD-3-Clause", "repo": "https://github.com/App-vNext/Polly", "is_direct": True},
    # transitive .NET dependencies
    {"name": "Microsoft.IdentityModel.Tokens", "version": "6.18.0", "license": "MIT", "repo": "https://github.com/AzureAD/azure-activedirectory-identitymodel-extensions-for-dotnet", "is_direct": False},
    {"name": "System.IdentityModel.Tokens.Jwt", "version": "6.18.0", "license": "MIT", "repo": "https://github.com/AzureAD/azure-activedirectory-identitymodel-extensions-for-dotnet", "is_direct": False},
    {"name": "Microsoft.EntityFrameworkCore.Abstractions", "version": "6.0.5", "license": "MIT", "repo": "https://github.com/dotnet/efcore", "is_direct": False},
    {"name": "Microsoft.EntityFrameworkCore.Relational", "version": "6.0.5", "license": "MIT", "repo": "https://github.com/dotnet/efcore", "is_direct": False},
    {"name": "Swashbuckle.AspNetCore.Swagger", "version": "6.3.0", "license": "MIT", "repo": "https://github.com/domaindrivendev/Swashbuckle.AspNetCore", "is_direct": False},
    {"name": "Swashbuckle.AspNetCore.SwaggerGen", "version": "6.3.0", "license": "MIT", "repo": "https://github.com/domaindrivendev/Swashbuckle.AspNetCore", "is_direct": False},
    {"name": "Microsoft.Extensions.Logging", "version": "6.0.0", "license": "MIT", "repo": "https://github.com/dotnet/runtime", "is_direct": False},
    {"name": "Microsoft.Extensions.Caching.Abstractions", "version": "6.0.0", "license": "MIT", "repo": "https://github.com/dotnet/runtime", "is_direct": False},
    {"name": "Microsoft.Extensions.DependencyInjection", "version": "6.0.0", "license": "MIT", "repo": "https://github.com/dotnet/runtime", "is_direct": False},
    {"name": "Microsoft.Extensions.Options", "version": "6.0.0", "license": "MIT", "repo": "https://github.com/dotnet/runtime", "is_direct": False},
    {"name": "System.Text.Json", "version": "6.0.0", "license": "MIT", "repo": "https://github.com/dotnet/runtime", "is_direct": False},
    {"name": "System.Text.Encodings.Web", "version": "6.0.0", "license": "MIT", "repo": "https://github.com/dotnet/runtime", "is_direct": False},
    {"name": "Microsoft.Bcl.AsyncInterfaces", "version": "6.0.0", "license": "MIT", "repo": "https://github.com/dotnet/runtime", "is_direct": False},
    {"name": "System.Threading.Tasks.Extensions", "version": "4.5.4", "license": "MIT", "repo": "https://github.com/dotnet/runtime", "is_direct": False}
]
dotnet_edges = [
    ("Microsoft.AspNetCore.Authentication.JwtBearer", "Microsoft.IdentityModel.Tokens"),
    ("Microsoft.AspNetCore.Authentication.JwtBearer", "System.IdentityModel.Tokens.Jwt"),
    ("Microsoft.EntityFrameworkCore", "Microsoft.EntityFrameworkCore.Abstractions"),
    ("Microsoft.EntityFrameworkCore", "Microsoft.EntityFrameworkCore.Relational"),
    ("Swashbuckle.AspNetCore", "Swashbuckle.AspNetCore.Swagger"),
    ("Swashbuckle.AspNetCore", "Swashbuckle.AspNetCore.SwaggerGen"),
    ("Microsoft.EntityFrameworkCore.Relational", "Microsoft.Extensions.Logging"),
    ("Microsoft.EntityFrameworkCore.Relational", "Microsoft.Extensions.Caching.Abstractions"),
    ("Microsoft.EntityFrameworkCore.Relational", "Microsoft.Extensions.DependencyInjection"),
    ("Microsoft.IdentityModel.Tokens", "System.Text.Json"),
    ("System.Text.Json", "System.Text.Encodings.Web"),
    ("System.Text.Json", "Microsoft.Bcl.AsyncInterfaces"),
    ("Microsoft.Bcl.AsyncInterfaces", "System.Threading.Tasks.Extensions"),
    ("Microsoft.Extensions.Options", "Microsoft.Extensions.DependencyInjection")
]

fixtures = [
    {
        "filename": "spring_boot_banking_api.json",
        "name": "spring-boot-banking-api",
        "tech": "maven",
        "dependencies": java_components,
        "edges": java_edges
    },
    {
        "filename": "spring_payment_service.json",
        "name": "spring-payment-service",
        "tech": "maven",
        "dependencies": java_components,
        "edges": java_edges
    },
    {
        "filename": "loan_processing_service.json",
        "name": "loan-processing-service",
        "tech": "maven",
        "dependencies": java_components,
        "edges": java_edges
    },
    {
        "filename": "express_backend.json",
        "name": "express-backend",
        "tech": "npm",
        "dependencies": nodejs_components,
        "edges": nodejs_edges
    },
    {
        "filename": "nestjs_gateway.json",
        "name": "nestjs-gateway",
        "tech": "npm",
        "dependencies": nodejs_components,
        "edges": nodejs_edges
    },
    {
        "filename": "react_frontend.json",
        "name": "react-frontend",
        "tech": "npm",
        "dependencies": nodejs_components,
        "edges": nodejs_edges
    },
    {
        "filename": "fastapi_authentication.json",
        "name": "fastapi-authentication",
        "tech": "pypi",
        "dependencies": python_components,
        "edges": python_edges
    },
    {
        "filename": "django_customer_portal.json",
        "name": "django-customer-portal",
        "tech": "pypi",
        "dependencies": python_components,
        "edges": python_edges
    },
    {
        "filename": "gin_treasury_api.json",
        "name": "gin-treasury-api",
        "tech": "golang",
        "dependencies": go_components,
        "edges": go_edges
    },
    {
        "filename": "notification_service.json",
        "name": "notification-service",
        "tech": "golang",
        "dependencies": go_components,
        "edges": go_edges
    },
    {
        "filename": "aspnet_core_identity_service.json",
        "name": "aspnet-core-identity-service",
        "tech": "nuget",
        "dependencies": dotnet_components,
        "edges": dotnet_edges
    },
    {
        "filename": "card_authorization_engine.json",
        "name": "card-authorization-engine",
        "tech": "nuget",
        "dependencies": dotnet_components,
        "edges": dotnet_edges
    }
]

out_dir = os.path.dirname(os.path.abspath(__file__))

for fix in fixtures:
    components = []
    bom_ref_map = {}
    
    for d in fix["dependencies"]:
        purl = f"pkg:{fix['tech']}/{d['name']}@{d['version']}"
        bom_ref_map[d['name']] = purl
        components.append({
            "name": d["name"],
            "version": d["version"],
            "type": "library",
            "purl": purl,
            "licenses": [{"license": {"id": d["license"]}}],
            "externalReferences": [{"type": "vcs", "url": d["repo"]}]
        })

    root_children = [bom_ref_map[d["name"]] for d in fix["dependencies"] if d["is_direct"]]
    ref_map = {"root-app": root_children}
    
    for edge in fix["edges"]:
        from_ref = bom_ref_map.get(edge[0])
        to_ref = bom_ref_map.get(edge[1])
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
                "name": fix["name"],
                "version": "1.0.0",
                "type": "application"
            }
        },
        "components": components,
        "dependencies": dependencies_section
    }

    out_path = os.path.join(out_dir, fix["filename"])
    with open(out_path, "w") as f:
        json.dump(sbom_data, f, indent=2)

print("Generated 12 industry-standard CycloneDX SBOM fixtures successfully!")
