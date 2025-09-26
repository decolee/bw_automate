#!/usr/bin/env python3
"""
Web Framework Patterns - Flask, FastAPI, Django patterns
Testing various web framework constructs and patterns
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

# === FLASK PATTERNS ===

try:
    from flask import Flask, request, jsonify, session, redirect, url_for, render_template, g
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import login_required, current_user
    from functools import wraps
    
    # Flask application patterns
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    db = SQLAlchemy(app)
    
    # Flask models
    class FlaskUser(db.Model):
        __tablename__ = 'users'
        
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(128))
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        posts = db.relationship('FlaskPost', backref='author', lazy=True)
        
        def __repr__(self):
            return f'<User {self.username}>'
    
    class FlaskPost(db.Model):
        __tablename__ = 'posts'
        
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(100), nullable=False)
        content = db.Column(db.Text, nullable=False)
        date_posted = db.Column(db.DateTime, default=datetime.utcnow)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Flask decorators
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.is_admin:
                return jsonify({'error': 'Admin access required'}), 403
            return f(*args, **kwargs)
        return decorated_function
    
    def rate_limit(max_requests=100, window=3600):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Rate limiting logic here
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    # Flask routes with various patterns
    @app.route('/')
    def flask_index():
        return render_template('index.html')
    
    @app.route('/api/users', methods=['GET', 'POST'])
    def flask_users():
        if request.method == 'POST':
            data = request.get_json()
            user = FlaskUser(
                username=data['username'],
                email=data['email']
            )
            db.session.add(user)
            db.session.commit()
            return jsonify({'id': user.id, 'username': user.username}), 201
        else:
            users = FlaskUser.query.all()
            return jsonify([
                {'id': u.id, 'username': u.username, 'email': u.email}
                for u in users
            ])
    
    @app.route('/api/users/<int:user_id>')
    def flask_get_user(user_id):
        user = FlaskUser.query.get_or_404(user_id)
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat()
        })
    
    @app.route('/api/posts')
    @login_required
    def flask_get_posts():
        posts = FlaskPost.query.join(FlaskUser).all()
        return jsonify([
            {
                'id': p.id,
                'title': p.title,
                'content': p.content,
                'author': p.author.username,
                'date_posted': p.date_posted.isoformat()
            }
            for p in posts
        ])
    
    @app.route('/admin/dashboard')
    @login_required
    @admin_required
    def flask_admin_dashboard():
        return jsonify({'message': 'Admin dashboard'})
    
    @app.route('/api/protected')
    @rate_limit(max_requests=50, window=3600)
    @login_required
    def flask_protected():
        return jsonify({'user_id': current_user.id})
    
    # Flask error handlers
    @app.errorhandler(404)
    def flask_not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def flask_internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Flask before/after request hooks
    @app.before_request
    def flask_before_request():
        g.start_time = datetime.utcnow()
    
    @app.after_request
    def flask_after_request(response):
        if hasattr(g, 'start_time'):
            duration = datetime.utcnow() - g.start_time
            response.headers['X-Response-Time'] = str(duration.total_seconds())
        return response

except ImportError:
    print("Flask not available")

# === FASTAPI PATTERNS ===

try:
    from fastapi import FastAPI, HTTPException, Depends, status, Query, Path, Body
    from fastapi.security import HTTPBearer, OAuth2PasswordBearer
    from pydantic import BaseModel, Field, validator
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    
    # FastAPI app
    fastapi_app = FastAPI(
        title="Test API",
        description="Comprehensive API testing",
        version="1.0.0"
    )
    
    # CORS middleware
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Pydantic models
    class UserCreate(BaseModel):
        username: str = Field(..., min_length=3, max_length=50)
        email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
        password: str = Field(..., min_length=8)
        
        @validator('username')
        def username_alphanumeric(cls, v):
            assert v.isalnum(), 'Username must be alphanumeric'
            return v
    
    class UserResponse(BaseModel):
        id: int
        username: str
        email: str
        created_at: datetime
        is_active: bool = True
        
        class Config:
            orm_mode = True
    
    class PostCreate(BaseModel):
        title: str = Field(..., max_length=100)
        content: str
        tags: List[str] = []
    
    class PostResponse(BaseModel):
        id: int
        title: str
        content: str
        author_id: int
        created_at: datetime
        tags: List[str]
        
        class Config:
            orm_mode = True
    
    # Dependency injection
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    
    async def get_current_user(token: str = Depends(oauth2_scheme)):
        # Token validation logic
        if token == "invalid":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"user_id": 1, "username": "testuser"}
    
    async def get_current_active_user(current_user: dict = Depends(get_current_user)):
        if not current_user.get("is_active", True):
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
    
    def get_admin_user(current_user: dict = Depends(get_current_active_user)):
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    
    # FastAPI routes
    @fastapi_app.get("/")
    async def fastapi_root():
        return {"message": "Hello World"}
    
    @fastapi_app.post("/users/", response_model=UserResponse)
    async def fastapi_create_user(user: UserCreate):
        # User creation logic
        return UserResponse(
            id=1,
            username=user.username,
            email=user.email,
            created_at=datetime.now()
        )
    
    @fastapi_app.get("/users/{user_id}", response_model=UserResponse)
    async def fastapi_get_user(
        user_id: int = Path(..., gt=0, description="The ID of the user to get"),
        current_user: dict = Depends(get_current_user)
    ):
        # Database query simulation
        return UserResponse(
            id=user_id,
            username="testuser",
            email="test@example.com",
            created_at=datetime.now()
        )
    
    @fastapi_app.get("/users/")
    async def fastapi_list_users(
        skip: int = Query(0, ge=0, description="Number of users to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
        search: Optional[str] = Query(None, description="Search term"),
        current_user: dict = Depends(get_current_user)
    ):
        return {"users": [], "total": 0, "skip": skip, "limit": limit}
    
    @fastapi_app.post("/posts/", response_model=PostResponse)
    async def fastapi_create_post(
        post: PostCreate,
        current_user: dict = Depends(get_current_active_user)
    ):
        return PostResponse(
            id=1,
            title=post.title,
            content=post.content,
            author_id=current_user["user_id"],
            created_at=datetime.now(),
            tags=post.tags
        )
    
    @fastapi_app.get("/admin/users/")
    async def fastapi_admin_list_users(admin_user: dict = Depends(get_admin_user)):
        return {"message": "Admin user list", "admin": admin_user["username"]}
    
    @fastapi_app.delete("/users/{user_id}")
    async def fastapi_delete_user(
        user_id: int,
        current_user: dict = Depends(get_admin_user)
    ):
        return {"message": f"User {user_id} deleted by {current_user['username']}"}
    
    # Background tasks
    from fastapi import BackgroundTasks
    
    def send_email_notification(email: str, message: str):
        # Email sending logic
        print(f"Sending email to {email}: {message}")
    
    @fastapi_app.post("/send-notification/")
    async def fastapi_send_notification(
        background_tasks: BackgroundTasks,
        email: str = Body(...),
        message: str = Body(...)
    ):
        background_tasks.add_task(send_email_notification, email, message)
        return {"message": "Notification sent in the background"}
    
    # Exception handlers
    @fastapi_app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        return JSONResponse(
            status_code=400,
            content={"message": f"Value error: {str(exc)}"}
        )
    
    # Middleware
    @fastapi_app.middleware("http")
    async def add_process_time_header(request, call_next):
        start_time = datetime.utcnow()
        response = await call_next(request)
        process_time = datetime.utcnow() - start_time
        response.headers["X-Process-Time"] = str(process_time.total_seconds())
        return response

except ImportError:
    print("FastAPI not available")

# === DJANGO PATTERNS (Simulated) ===

class DjangoPatterns:
    """Simulated Django patterns for testing"""
    
    def django_models(self):
        """Django model patterns"""
        patterns = [
            # Model definitions
            """
            class User(models.Model):
                username = models.CharField(max_length=150, unique=True)
                email = models.EmailField(unique=True)
                first_name = models.CharField(max_length=30, blank=True)
                last_name = models.CharField(max_length=150, blank=True)
                is_active = models.BooleanField(default=True)
                date_joined = models.DateTimeField(default=timezone.now)
                
                class Meta:
                    ordering = ['username']
                    verbose_name = 'User'
                    verbose_name_plural = 'Users'
                
                def __str__(self):
                    return self.username
                
                def get_absolute_url(self):
                    return reverse('user-detail', kwargs={'pk': self.pk})
            """,
            
            # Model with relationships
            """
            class Post(models.Model):
                title = models.CharField(max_length=200)
                content = models.TextField()
                author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
                created_at = models.DateTimeField(auto_now_add=True)
                updated_at = models.DateTimeField(auto_now=True)
                tags = models.ManyToManyField('Tag', blank=True)
                
                class Meta:
                    ordering = ['-created_at']
                
                def save(self, *args, **kwargs):
                    # Custom save logic
                    super().save(*args, **kwargs)
            """,
            
            # Custom manager
            """
            class PublishedPostManager(models.Manager):
                def get_queryset(self):
                    return super().get_queryset().filter(status='published')
            
            class Post(models.Model):
                # ... fields ...
                objects = models.Manager()  # Default manager
                published = PublishedPostManager()  # Custom manager
            """
        ]
        return patterns
    
    def django_views(self):
        """Django view patterns"""
        patterns = [
            # Function-based views
            """
            def user_list(request):
                users = User.objects.all()
                return render(request, 'users/list.html', {'users': users})
            
            def user_detail(request, pk):
                user = get_object_or_404(User, pk=pk)
                return render(request, 'users/detail.html', {'user': user})
            
            @login_required
            def user_create(request):
                if request.method == 'POST':
                    form = UserForm(request.POST)
                    if form.is_valid():
                        user = form.save()
                        return redirect('user-detail', pk=user.pk)
                else:
                    form = UserForm()
                return render(request, 'users/create.html', {'form': form})
            """,
            
            # Class-based views
            """
            class UserListView(ListView):
                model = User
                template_name = 'users/list.html'
                context_object_name = 'users'
                paginate_by = 25
                
                def get_queryset(self):
                    return User.objects.filter(is_active=True)
            
            class UserDetailView(DetailView):
                model = User
                template_name = 'users/detail.html'
            
            class UserCreateView(LoginRequiredMixin, CreateView):
                model = User
                form_class = UserForm
                template_name = 'users/create.html'
                success_url = reverse_lazy('user-list')
            """,
            
            # API views
            """
            class UserAPIView(APIView):
                permission_classes = [IsAuthenticated]
                
                def get(self, request):
                    users = User.objects.all()
                    serializer = UserSerializer(users, many=True)
                    return Response(serializer.data)
                
                def post(self, request):
                    serializer = UserSerializer(data=request.data)
                    if serializer.is_valid():
                        serializer.save()
                        return Response(serializer.data, status=201)
                    return Response(serializer.errors, status=400)
            """
        ]
        return patterns
    
    def django_forms(self):
        """Django form patterns"""
        patterns = [
            """
            class UserForm(forms.ModelForm):
                password = forms.CharField(widget=forms.PasswordInput)
                password_confirm = forms.CharField(widget=forms.PasswordInput)
                
                class Meta:
                    model = User
                    fields = ['username', 'email', 'first_name', 'last_name']
                
                def clean_password_confirm(self):
                    password = self.cleaned_data.get('password')
                    password_confirm = self.cleaned_data.get('password_confirm')
                    if password and password_confirm and password != password_confirm:
                        raise forms.ValidationError("Passwords don't match")
                    return password_confirm
                
                def save(self, commit=True):
                    user = super().save(commit=False)
                    user.set_password(self.cleaned_data['password'])
                    if commit:
                        user.save()
                    return user
            """,
            
            """
            class ContactForm(forms.Form):
                name = forms.CharField(max_length=100)
                email = forms.EmailField()
                subject = forms.CharField(max_length=200)
                message = forms.CharField(widget=forms.Textarea)
                
                def clean_email(self):
                    email = self.cleaned_data['email']
                    if not email.endswith('@example.com'):
                        raise forms.ValidationError('Only @example.com emails allowed')
                    return email
            """
        ]
        return patterns

# === WEB FRAMEWORK UTILITIES ===

class RequestValidator:
    """Request validation utilities"""
    
    @staticmethod
    def validate_json_data(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """Validate JSON request data"""
        errors = {}
        
        for field in required_fields:
            if field not in data:
                errors[field] = "This field is required"
            elif not data[field]:
                errors[field] = "This field cannot be empty"
        
        if errors:
            raise ValueError(f"Validation errors: {errors}")
        
        return data
    
    @staticmethod
    def validate_pagination(page: int = 1, per_page: int = 20) -> tuple:
        """Validate pagination parameters"""
        page = max(1, page)
        per_page = min(max(1, per_page), 100)  # Limit to 100 items per page
        return page, per_page

class ResponseFormatter:
    """Response formatting utilities"""
    
    @staticmethod
    def success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
        """Format success response"""
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def error_response(message: str, errors: Optional[Dict] = None, status_code: int = 400) -> Dict[str, Any]:
        """Format error response"""
        response = {
            "success": False,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if errors:
            response["errors"] = errors
        
        return response
    
    @staticmethod
    def paginated_response(items: List[Any], total: int, page: int, per_page: int) -> Dict[str, Any]:
        """Format paginated response"""
        return {
            "success": True,
            "data": items,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
                "has_next": page * per_page < total,
                "has_prev": page > 1
            },
            "timestamp": datetime.utcnow().isoformat()
        }

# Authentication and authorization utilities
class AuthUtils:
    """Authentication utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password for storage"""
        import hashlib
        salt = "static_salt_for_testing"  # In production, use random salt
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hash_value: str) -> bool:
        """Verify password against hash"""
        return AuthUtils.hash_password(password) == hash_value
    
    @staticmethod
    def generate_token(user_id: int, expires_in: int = 3600) -> str:
        """Generate JWT-like token"""
        import base64
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in)
        }
        # Simplified token generation (use proper JWT in production)
        token_data = json.dumps(payload, default=str)
        return base64.b64encode(token_data.encode()).decode()
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode token"""
        try:
            import base64
            token_data = base64.b64decode(token.encode()).decode()
            payload = json.loads(token_data)
            
            exp_time = datetime.fromisoformat(payload["exp"])
            if datetime.utcnow() > exp_time:
                return None  # Token expired
            
            return payload
        except:
            return None  # Invalid token

# WebSocket patterns (if available)
try:
    import websockets
    
    class WebSocketHandler:
        """WebSocket connection handler"""
        
        def __init__(self):
            self.connections = set()
        
        async def register(self, websocket):
            """Register new connection"""
            self.connections.add(websocket)
        
        async def unregister(self, websocket):
            """Unregister connection"""
            self.connections.discard(websocket)
        
        async def broadcast(self, message: str):
            """Broadcast message to all connections"""
            if self.connections:
                await asyncio.gather(
                    *[ws.send(message) for ws in self.connections],
                    return_exceptions=True
                )
        
        async def handle_connection(self, websocket, path):
            """Handle WebSocket connection"""
            await self.register(websocket)
            try:
                async for message in websocket:
                    # Echo message back to all clients
                    await self.broadcast(f"Echo: {message}")
            finally:
                await self.unregister(websocket)

except ImportError:
    print("WebSockets not available")

# Testing and demonstration
if __name__ == "__main__":
    print("=== Web Framework Patterns Testing ===")
    
    # Test Django patterns
    django_patterns = DjangoPatterns()
    print("\nDjango Model Patterns:")
    for i, pattern in enumerate(django_patterns.django_models(), 1):
        print(f"  Pattern {i}: {pattern[:50]}...")
    
    # Test validation
    validator = RequestValidator()
    try:
        data = {"username": "test", "email": "test@example.com"}
        validated = validator.validate_json_data(data, ["username", "email", "password"])
    except ValueError as e:
        print(f"\nValidation error: {e}")
    
    # Test response formatting
    formatter = ResponseFormatter()
    success_resp = formatter.success_response({"id": 1, "name": "Test"})
    print(f"\nSuccess response: {success_resp}")
    
    error_resp = formatter.error_response("Validation failed", {"email": "Invalid email"})
    print(f"Error response: {error_resp}")
    
    # Test authentication
    auth = AuthUtils()
    password_hash = auth.hash_password("test_password")
    print(f"\nPassword hash: {password_hash[:20]}...")
    
    token = auth.generate_token(user_id=123)
    print(f"Generated token: {token[:30]}...")
    
    verified = auth.verify_token(token)
    print(f"Token verification: {verified}")
    
    print("\n=== Web framework testing completed! ===")