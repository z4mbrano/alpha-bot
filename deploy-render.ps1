# Script para deploy após migração para Render
# Execute este script para fazer commit e push das mudanças

Write-Host "🚀 DEPLOY RENDER - Atualizando Frontend" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""

# Verificar se git está disponível
try {
    git --version | Out-Null
    Write-Host "✅ Git encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Git não encontrado. Por favor, instale o Git primeiro." -ForegroundColor Red
    Write-Host "Download: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Verificar status
Write-Host "📋 Verificando status do repositório..." -ForegroundColor Yellow
git status

Write-Host ""
Write-Host "📦 Adicionando todas as mudanças..." -ForegroundColor Yellow
git add .

Write-Host ""
Write-Host "💾 Fazendo commit das mudanças..." -ForegroundColor Yellow
git commit -m "Migração completa para Render - Backend funcionando em https://alpha-bot-oglo.onrender.com"

Write-Host ""
Write-Host "🌐 Enviando para repositório remoto..." -ForegroundColor Yellow
git push origin main

Write-Host ""
Write-Host "✅ Deploy concluído!" -ForegroundColor Green
Write-Host "🔄 Aguarde alguns minutos para o Vercel redeployar o frontend" -ForegroundColor Cyan
Write-Host "🌐 Verifique em: https://alpha-bot-six.vercel.app" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 Backend ativo em: https://alpha-bot-oglo.onrender.com" -ForegroundColor Green

# Testar backend
Write-Host ""
Write-Host "🔍 Testando backend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://alpha-bot-oglo.onrender.com/api/health" -Method Get
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend respondendo corretamente!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Backend retornou status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Erro ao conectar com backend: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host "1. Aguarde o Vercel redeployar (1-3 minutos)" -ForegroundColor White
Write-Host "2. Teste a aplicação em https://alpha-bot-six.vercel.app" -ForegroundColor White
Write-Host "3. Verifique se não há mais erros de CORS" -ForegroundColor White