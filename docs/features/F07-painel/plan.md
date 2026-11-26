# F07 — Painel: plano

Spec: `spec.md`. Branch `feat/f07-painel` (wave paralela W5). **Primeiro commit e push logo na etapa 1.** Testes em `tests/test_f07_panel.py`.

1. **Métricas.** Ingressos inseridos por SQL: `test_metrics_counts` (2 confirmed sendo 1 com check-in, 1 pending, 1 declined, 1 cancelled, 1 refunded → confirmed 2, pending 1, checkins 1, refunded 1), `test_revenue_uses_ticket_price` (confirmed 10000 + 10000 + 15000 → 35000; refunded 10000 e declined 10000 fora), `test_available_cancelled_zero` (evento `cancelled` → 0).
2. **Parcial.** `test_panel_rendered_on_manage_page` (os 6 rótulos e `data-metric`; Receita `R$ 350,00`), `test_other_org_cannot_see_panel` (B → 404, sem `id="panel"`).
3. **Integração.** `test_web_and_api_purchases_count` (XF-13/XF-14: 1 compra vitrine 0001 + 1 API 0001 confirmadas + 1 API 0003 pendente → Confirmados 2, Pendentes 1, Vagas = lotação − 3), `test_price_change_revenue` (XF-13: compra a R$100, edita para R$150, compra → Receita `R$ 250,00`), `test_capacity_increase_reflects_available` (XF-12: edita lotação de 2 para 3 → Vagas sobe 1).
4. `./scripts/gates.sh` verde, push, PR.
