/**
 * ChartRenderer - Renderiza gráficos interativos com Recharts
 * Sprint 2 Feature 3: Gráficos Automáticos
 */

import React from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { ChartData } from '../types'

interface ChartRendererProps {
  chart: ChartData
}

export default function ChartRenderer({ chart }: ChartRendererProps) {
  const { type, data, x_axis, y_axis, title } = chart

  // Cores do tema (var CSS)
  const primaryColor = 'hsl(221, 83%, 53%)'  // var(--accent)
  const gridColor = 'hsl(214, 32%, 91%)'     // var(--border)

  // Componente comum: Tooltip customizado
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-3 shadow-lg">
          <p className="text-sm font-semibold text-[var(--text)] mb-1">
            {payload[0].payload[x_axis]}
          </p>
          <p className="text-xs text-[var(--accent)] font-bold">
            {y_axis}: {payload[0].value.toLocaleString('pt-BR')}
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="my-4 p-4 bg-[var(--bg)]/30 rounded-lg border border-[var(--border)]">
      {title && (
        <h4 className="text-sm font-bold text-[var(--text)] mb-3">{title}</h4>
      )}
      
      <ResponsiveContainer width="100%" height={300}>
        {type === 'line' ? (
          <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis 
              dataKey={x_axis} 
              stroke="var(--muted)"
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              stroke="var(--muted)"
              style={{ fontSize: '12px' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ fontSize: '12px' }}
              iconType="line"
            />
            <Line
              type="monotone"
              dataKey={y_axis}
              stroke={primaryColor}
              strokeWidth={2}
              dot={{ fill: primaryColor, r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        ) : type === 'bar' ? (
          <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis 
              dataKey={x_axis} 
              stroke="var(--muted)"
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              stroke="var(--muted)"
              style={{ fontSize: '12px' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ fontSize: '12px' }}
              iconType="rect"
            />
            <Bar 
              dataKey={y_axis} 
              fill={primaryColor}
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        ) : null}
      </ResponsiveContainer>
    </div>
  )
}
