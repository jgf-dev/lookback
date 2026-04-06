import '@testing-library/jest-dom'

// Global fetch mock – reset between tests automatically
global.fetch = jest.fn()

beforeEach(() => {
  ;(global.fetch as jest.Mock).mockReset()
})