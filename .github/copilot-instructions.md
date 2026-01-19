# AI Copilot Instructions for GDF_V2

## Architecture Overview

GDF_V2 is a Django web application with multi-database support and Streamlit analytics dashboards. The system has three core components:

1. **Django Web App** (`GDF_PJT/`): Multi-tenant ERP for managing customers, companies, and solutions with role-based access
2. **PostgreSQL Multi-Database** (`GDF_DEV` + `REPROCESSAMENTO_DEV`): Separated via `DATABASE_ROUTERS` in `routers.py`
3. **Streamlit Dashboards** (`streamlit/Compras/` & `streamlit/Vendas/`): Analytics for purchases and sales

## Database Routing Pattern

Models are split across two database schemas, routed automatically via `GDFRouter` and `ReprocessamentoRouter`:
- Models in `app.db_GDF.*` → `default` database (`GDF_DEV`)
- Models in `app.db_Reprocessamento.*` → `reprocessamento` database (`REPROCESSAMENTO_DEV`)

When adding models, place them in the correct module to ensure router directs queries to the right database.

## Key Business Logic

The `Cl_Gdf` class ([app/classes/Gdf.py](app/classes/Gdf.py)) is the core business entity:
- **Initialization**: Loads user's companies, groups, and access rights on login
- **Session Storage**: Solutions (`t_solucoes`) and customer code (`cod_cliente`) stored in `request.session` 
- **JWT Token Generation**: Creates 30-minute tokens for Streamlit dashboard authentication
- **Access Control**: Queries `SolucoesAcesso` (solution level) and `SubsolucoesAcesso` (subsolution level via groups)

After login, `Cl_Gdf().get_dados(user)` populates session; views check `request.session.get('t_solucoes')` for authorized modules.

## Critical Workflows

### Local Development
```bash
cd GDF_PJT
python manage.py runserver  # Starts on port 8000
```

### Database Management
- Migrations stored in `app/migrations/`
- PostgreSQL credentials in `settings.py` (currently hardcoded; migrate to env vars)
- Toggle between PostgreSQL and SQLite in `settings.py` database config (lines 75-110)

### Streamlit Dashboards
- Located in `streamlit/Compras/` and `streamlit/Vendas/`
- Initialize Django in `@st.cache_resource` before importing Django models
- Uses helper modules: `tp_lists.py` (data queries), `tp_graficos.py` (chart generation)

## Session & Authentication

- Login URL: `/Login/` → redirects to `/home/` on success
- Session timeout: 30 minutes (`SESSION_COOKIE_AGE = 1800`)
- Decorator usage: `@login_required` protects views requiring authentication
- Context processor `solucoes_context` injects session data into all templates

## URL Structure

Main routes defined in [GDF_PJT/urls.py](GDF_PJT/urls.py):
- `/Login/` - Authentication entry point
- `/Home/` - Main dashboard (authenticated)
- `/Usuarios/`, `/Empresas/`, `/Clientes/` - Data management modules
- `/Dashboard/` - Sales/Purchases analytics
- Modal routes: `/usuario_ins/`, `/usuarios/<id>/` for CRUD operations

## Static & Template Organization

- **Static**: `app/static/css/`, `app/static/js/` (organized by feature: `Style_Usuarios.css`, `Script_Dashboard.js`)
- **Templates**: `app/templates/` with subdirectories mirroring URL paths (`Usuarios/`, `Empresas/`, `Dashboard/`)
- CSS/JS naming convention: `Style_<Module>.css` and `Script_<Module>.js`

## View & CRUD Patterns

All views follow consistent patterns (see [app/views.py](app/views.py)):

**List Views** (e.g., `Dm_Usuarios_view`):
- Use `@login_required(login_url='Login')` decorator
- Extract `cod_cliente` from session: `Cod_cliente = request.session.get('cod_cliente', None)`
- Instantiate `Cl_Gdf()` to call data retrieval methods like `get_usuarios()`, `get_empresas()`
- Support search filtering with `request.GET.get('Buscar')`
- Paginate results: `Paginator(data, 30)` 
- Render with context dict containing paginated objects and lookup lists

**Modal Insert/Update**:
- Insert (POST): Extract form data, call `ClGdf.ins_usuario()`, redirect to list view
- Update: GET returns `JsonResponse` with user data; POST updates and redirects
- Always pass `cod_cliente` from session to `Cl_Gdf` methods for multi-tenancy enforcement

**Access Control**:
- Session variables injected by `solucoes_context` processor
- Always validate `request.session.get('cod_cliente')` before database operations

## Dependencies

Key packages: Django 6.0.1, PostgreSQL driver (psycopg2-binary), Streamlit 1.52.2, Pandas 2.3.3, PyJWT for tokens. See `requirements.txt` for full list.

## Common Pitfalls

- **Database selection**: Ensure models are in correct `db_GDF` or `db_Reprocessamento` modules or queries hit wrong database
- **Session validation**: Always extract `cod_cliente` from session before calling `Cl_Gdf` methods—this enforces multi-tenant isolation
- **Credentials**: Database password exposed in settings.py—move to environment variables for production
- **Streamlit Django setup**: Must call `django.setup()` after adding project path in `@st.cache_resource`; always import models after setup
- **Redirect loops**: Modal update endpoints return JsonResponse on GET but redirect on POST—client must handle both
